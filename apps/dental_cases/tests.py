from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .exceptions import DashboardMetricsError
from .models import DentalCase
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

        # El polling depende de que estas zonas sigan existiendo.
        self.assertIn("dashboard-metrics", content)
        self.assertIn("dashboard-stages", content)
        self.assertIn(DashboardView.METRICS_ERROR_MESSAGE, content)
