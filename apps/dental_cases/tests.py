from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.laboratories.models import Laboratory

from .exceptions import DashboardMetricsError
from .models import DentalCase
from .permissions import can_access_case
from .services import DentalCaseService
from .views import DashboardView


def build_case(case_number, status, **overrides):
    """
    Creates a dental case with sensible defaults for the tests.
    """

    data = {
        "clinic_name": "Clinica Prueba",
        "requested_by": "santiago_test",
        "service_type": "CROWN",
        "description": "Prueba de dashboard",
        "due_date": timezone.now().date() + timedelta(days=7),
    }

    data.update(overrides)

    return DentalCase.objects.create(
        case_number=case_number,
        status=status,
        **data,
    )


class DashboardMetricsTests(TestCase):

    def setUp(self):

        # 2 casos pendientes
        build_case("CASE-001", DentalCase.Status.SUBMITTED)
        build_case("CASE-002", DentalCase.Status.IN_REVIEW)

        # 1 caso en proceso
        build_case("CASE-003", DentalCase.Status.IN_PROGRESS)

        # 1 caso completado
        build_case("CASE-004", DentalCase.Status.COMPLETED)

        # Los indicadores son de todo el laboratorio, asi que un caso
        # pedido por otro usuario tambien debe contarse.
        build_case(
            "CASE-005",
            DentalCase.Status.SUBMITTED,
            requested_by="otro_usuario",
        )

    def test_dashboard_metrics_calculation(self):
        """
        Los indicadores cuentan los casos de todo el laboratorio.
        """

        metrics = DentalCaseService.get_dashboard_metrics()

        self.assertEqual(metrics["pending"], 3)
        self.assertEqual(metrics["in_progress"], 1)
        self.assertEqual(metrics["completed"], 1)
        self.assertEqual(metrics["total_active"], 4)

    def test_metrics_error_is_raised_when_the_query_fails(self):
        """
        Un fallo de la capa de datos se traduce a DashboardMetricsError.
        """

        with patch(
            "apps.dental_cases.services.DentalCaseSelector"
            ".get_dashboard_metrics",
            side_effect=DatabaseError("database is locked"),
        ):

            # El fallo original queda registrado para poder depurarlo.
            with self.assertLogs(
                "apps.dental_cases.services",
                level="ERROR",
            ):

                with self.assertRaises(DashboardMetricsError):
                    DentalCaseService.get_dashboard_metrics()


class DashboardViewTests(TestCase):

    def setUp(self):

        self.url = reverse("dashboard")

        self.user = User.objects.create_user(
            username="santiago_test",
            password="clave-de-prueba",
        )

    def test_dashboard_requires_login(self):
        """
        Un usuario anonimo es redirigido al login.
        """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("dashboard-metrics", response.content.decode())

    def test_dashboard_shows_metrics(self):
        """
        Con la consulta sana, el dashboard muestra los indicadores.
        """

        self.client.force_login(self.user)

        build_case("CASE-001", DentalCase.Status.IN_PROGRESS)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["metrics_error"])
        self.assertEqual(response.context["in_progress"], 1)

    def test_dashboard_shows_message_when_metrics_fail(self):
        """
        Si los indicadores fallan, el dashboard sigue respondiendo 200
        y muestra un mensaje en lugar de las tarjetas.
        """

        self.client.force_login(self.user)

        with patch(
            "apps.dental_cases.views.DentalCaseService"
            ".get_dashboard_metrics",
            side_effect=DashboardMetricsError("boom"),
        ):

            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["metrics_error"],
            DashboardView.METRICS_ERROR_MESSAGE,
        )

        content = response.content.decode()

        # El polling depende de que esta zona siga existiendo.
        self.assertIn("dashboard-metrics", content)
        self.assertIn(DashboardView.METRICS_ERROR_MESSAGE, content)


class LaboratoryDecisionAndAssignmentTests(TestCase):
    def setUp(self):
        self.laboratory = Laboratory.objects.create(
            name="Dental Lab", email="lab@example.com", phone="1", city="Medellin",
            address="Street 1", service="CROWN",
        )
        user_model = get_user_model()
        self.technician = user_model.objects.create_user("tech", password="test")
        self.other_technician = user_model.objects.create_user("other", password="test")
        self.laboratory.technicians.add(self.technician)
        self.case = DentalCase.objects.create(
            case_number="DF-100", clinic_name="Clinic", requested_by="Dr. Test",
            laboratory=self.laboratory, service_type="CROWN", description="Case",
            due_date=date.today(),
        )

    def test_accepting_case_allows_a_laboratory_technician_assignment(self):
        DentalCaseService.accept(self.case)
        assignment = DentalCaseService.assign_technician(self.case, self.technician)
        self.assertEqual(assignment.technician, self.technician)
        self.assertEqual(self.case.acceptance_status, DentalCase.AcceptanceStatus.ACCEPTED)

    def test_rejected_case_cannot_start_production(self):
        DentalCaseService.reject(self.case, "Missing scan")
        with self.assertRaisesMessage(ValueError, "Production can only begin"):
            DentalCaseService.start_production(self.case)

    def test_cannot_assign_technician_from_another_laboratory(self):
        DentalCaseService.accept(self.case)
        with self.assertRaisesMessage(ValueError, "does not belong"):
            DentalCaseService.assign_technician(self.case, self.other_technician)


def build_laboratory(name, email):
    """
    Creates a laboratory with sensible defaults for the tests.
    """

    return Laboratory.objects.create(
        name=name,
        email=email,
        phone="1",
        city="Medellin",
        address="Calle 1",
        service="CROWN",
    )


def listed_numbers(response):
    """
    Returns the case numbers shown by a case list response, sorted.
    """

    return sorted(
        case.case_number
        for case in response.context["dental_cases"]
    )


class CaseListAccessTests(TestCase):
    """
    El listado solo muestra los casos que el usuario puede ver.
    """

    def setUp(self):

        self.url = reverse("dental_case_list")

        self.propio = build_laboratory("Lab Propio", "propio@test.com")
        self.ajeno = build_laboratory("Lab Ajeno", "ajeno@test.com")

        self.user = User.objects.create_user("tecnico", password="clave")
        self.propio.authorized_users.add(self.user)

        build_case("A-001", DentalCase.Status.IN_PROGRESS, laboratory=self.propio)
        build_case("A-002", DentalCase.Status.SUBMITTED, laboratory=self.ajeno)
        build_case("A-003", DentalCase.Status.SUBMITTED, created_by=self.user)
        build_case("A-004", DentalCase.Status.SUBMITTED)

    def test_list_requires_login(self):
        """
        Un usuario anonimo es redirigido al login.
        """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_user_sees_own_laboratory_and_own_cases(self):
        """
        Ve los casos de su laboratorio y los que registro, nada mas.
        """

        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(listed_numbers(response), ["A-001", "A-003"])

    def test_superuser_sees_every_case(self):

        admin = User.objects.create_superuser(
            "admin", password="clave", email="admin@test.com"
        )

        self.client.force_login(admin)

        response = self.client.get(self.url)

        self.assertEqual(len(listed_numbers(response)), 4)

    def test_user_without_cases_sees_the_empty_message(self):
        """
        Sin casos propios ni laboratorio, la lista va vacia y lo dice.
        """

        nuevo = User.objects.create_user("nuevo", password="clave")

        self.client.force_login(nuevo)

        response = self.client.get(self.url)

        self.assertEqual(listed_numbers(response), [])
        self.assertIn(
            "No dental cases registered",
            response.content.decode(),
        )

    def test_list_rule_matches_the_case_access_rule(self):
        """
        El listado y el acceso a un caso aplican la misma regla: un
        caso aparece en la lista si y solo si el usuario puede abrirlo.
        """

        self.client.force_login(self.user)

        listed = set(listed_numbers(self.client.get(self.url)))

        for case in DentalCase.objects.all():
            with self.subTest(case=case.case_number):
                self.assertEqual(
                    case.case_number in listed,
                    can_access_case(self.user, case),
                )


class CaseSearchTests(TestCase):
    """
    FR-25: busqueda de casos por numero, clinica y solicitante.
    """

    def setUp(self):

        self.url = reverse("dental_case_list")

        propio = build_laboratory("Lab Propio", "propio@test.com")
        ajeno = build_laboratory("Lab Ajeno", "ajeno@test.com")

        self.user = User.objects.create_user("tecnico", password="clave")
        propio.authorized_users.add(self.user)

        build_case(
            "DF-1001",
            DentalCase.Status.IN_PROGRESS,
            clinic_name="Clinica Sonrisa",
            requested_by="Dra. Martinez",
            laboratory=propio,
        )
        build_case(
            "DF-1002",
            DentalCase.Status.SUBMITTED,
            clinic_name="Odonto Centro",
            requested_by="Dr. Perez",
            laboratory=propio,
        )
        build_case(
            "XR-2001",
            DentalCase.Status.COMPLETED,
            clinic_name="Clinica Norte",
            requested_by="Dra. Gomez",
            laboratory=propio,
        )

        # Coincide con varias busquedas, pero es de otro laboratorio.
        build_case(
            "DF-9999",
            DentalCase.Status.IN_PROGRESS,
            clinic_name="Clinica Sonrisa",
            requested_by="Dra. Martinez",
            laboratory=ajeno,
        )

        self.client.force_login(self.user)

    def search(self, term):
        return self.client.get(self.url, {"q": term})

    def test_search_by_case_number(self):

        self.assertEqual(
            listed_numbers(self.search("XR-2001")),
            ["XR-2001"],
        )

    def test_search_by_partial_case_number(self):

        self.assertEqual(
            listed_numbers(self.search("DF-10")),
            ["DF-1001", "DF-1002"],
        )

    def test_search_by_clinic(self):

        self.assertEqual(
            listed_numbers(self.search("Odonto")),
            ["DF-1002"],
        )

    def test_search_by_requester(self):

        self.assertEqual(
            listed_numbers(self.search("Gomez")),
            ["XR-2001"],
        )

    def test_search_ignores_upper_and_lower_case(self):

        self.assertEqual(
            listed_numbers(self.search("cLiNiCa nOrTe")),
            ["XR-2001"],
        )

    def test_search_never_returns_another_laboratory(self):
        """
        DF-9999 coincide con el termino, pero el usuario no puede verlo.
        """

        self.assertEqual(
            listed_numbers(self.search("Sonrisa")),
            ["DF-1001"],
        )

    def test_blank_search_returns_every_visible_case(self):

        self.assertEqual(
            listed_numbers(self.search("   ")),
            ["DF-1001", "DF-1002", "XR-2001"],
        )

    def test_search_without_results_informs_the_user(self):

        response = self.search("inexistente")

        self.assertEqual(listed_numbers(response), [])
        self.assertIn(
            "No dental cases match your search",
            response.content.decode(),
        )

    def test_search_term_stays_in_the_form(self):

        response = self.search("Sonrisa")

        self.assertIn('value="Sonrisa"', response.content.decode())


class CaseFilterTests(TestCase):
    """
    FR-26: filtros por estado, servicio y rango de fecha de entrega.
    """

    def setUp(self):

        self.url = reverse("dental_case_list")

        self.propio = build_laboratory("Lab Propio", "propio@test.com")
        ajeno = build_laboratory("Lab Ajeno", "ajeno@test.com")

        self.user = User.objects.create_user("tecnico", password="clave")
        self.propio.authorized_users.add(self.user)

        self.hoy = timezone.now().date()

        casos = [
            ("F-001", DentalCase.Status.IN_PROGRESS, "CROWN", 2),
            ("F-002", DentalCase.Status.IN_PROGRESS, "BRIDGE", 10),
            ("F-003", DentalCase.Status.COMPLETED, "CROWN", 20),
            ("F-004", DentalCase.Status.SUBMITTED, "IMPLANT", -3),
        ]

        for numero, estado, servicio, dias in casos:
            build_case(
                numero,
                estado,
                service_type=servicio,
                due_date=self.hoy + timedelta(days=dias),
                laboratory=self.propio,
            )

        # Cumple casi todos los filtros, pero es de otro laboratorio.
        build_case(
            "F-999",
            DentalCase.Status.IN_PROGRESS,
            service_type="CROWN",
            due_date=self.hoy + timedelta(days=2),
            laboratory=ajeno,
        )

        self.client.force_login(self.user)

    def filtered(self, **params):
        return self.client.get(self.url, params)

    def dia(self, dias):
        return (self.hoy + timedelta(days=dias)).isoformat()

    def test_filter_by_status(self):

        self.assertEqual(
            listed_numbers(self.filtered(status="IN_PROGRESS")),
            ["F-001", "F-002"],
        )

    def test_filter_by_service_type(self):

        self.assertEqual(
            listed_numbers(self.filtered(service_type="CROWN")),
            ["F-001", "F-003"],
        )

    def test_filter_by_due_date_range(self):

        response = self.filtered(due_from=self.dia(0), due_to=self.dia(15))

        self.assertEqual(listed_numbers(response), ["F-001", "F-002"])

    def test_filter_by_open_ended_due_dates(self):
        """
        El rango funciona con un solo extremo.
        """

        self.assertEqual(
            listed_numbers(self.filtered(due_from=self.dia(5))),
            ["F-002", "F-003"],
        )
        self.assertEqual(
            listed_numbers(self.filtered(due_to=self.dia(0))),
            ["F-004"],
        )

    def test_filters_combine(self):
        """
        Los filtros se aplican juntos, no uno u otro.
        """

        response = self.filtered(status="IN_PROGRESS", service_type="CROWN")

        self.assertEqual(listed_numbers(response), ["F-001"])

    def test_filters_combine_with_the_search(self):

        response = self.filtered(q="F-00", status="COMPLETED")

        self.assertEqual(listed_numbers(response), ["F-003"])

    def test_applied_filters_are_shown_and_can_be_cleared(self):

        response = self.filtered(status="IN_PROGRESS", service_type="CROWN")

        content = response.content.decode()

        self.assertIn("Status: In Progress", content)
        self.assertIn("Service: Dental Crown", content)
        self.assertIn("Clear filters", content)

    def test_list_without_filters_offers_nothing_to_clear(self):

        response = self.client.get(self.url)

        self.assertNotIn("Clear filters", response.content.decode())

    def test_inverted_date_range_is_rejected(self):
        """
        Un rango invertido se informa y no filtra la lista.
        """

        response = self.filtered(due_from=self.dia(10), due_to=self.dia(1))

        self.assertIn("due_to", response.context["form"].errors)
        self.assertEqual(len(listed_numbers(response)), 4)
        self.assertIn(
            "The end date cannot be earlier than the start date.",
            response.content.decode(),
        )

    def test_unknown_status_does_not_break_the_list(self):

        response = self.filtered(status="NO_EXISTE")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(listed_numbers(response)), 4)

    def test_filter_without_results_informs_the_user(self):

        response = self.filtered(status="CANCELLED")

        self.assertEqual(listed_numbers(response), [])
        self.assertIn(
            "No dental cases match your search",
            response.content.decode(),
        )

    def test_laboratory_inbox_filters_too(self):
        """
        La bandeja del laboratorio usa el mismo buscador y filtros.
        """

        url = reverse("laboratory_case_inbox", args=[self.propio.id])

        response = self.client.get(url, {"status": "COMPLETED"})

        self.assertEqual(listed_numbers(response), ["F-003"])
