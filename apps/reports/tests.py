from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.dental_cases.models import DentalCase
from apps.workflow.models import Workflow

from .exceptions import ReportGenerationError
from .forms import ReportFilterForm
from .services import ReportService
from .views import OperationalReportsView


def build_case(case_number, status, created_at=None, **overrides):
    """
    Creates a dental case with sensible defaults for the tests.
    """

    data = {
        "clinic_name": "Clinica Prueba",
        "requested_by": "santiago_test",
        "service_type": "CROWN",
        "description": "Prueba de reportes",
        "due_date": timezone.now().date() + timedelta(days=7),
    }

    data.update(overrides)

    case = DentalCase.objects.create(
        case_number=case_number,
        status=status,
        **data,
    )

    if created_at:
        # created_at is auto_now_add, so it has to be forced afterwards.
        DentalCase.objects.filter(pk=case.pk).update(created_at=created_at)
        case.refresh_from_db()

    return case


class ProductionReportTests(TestCase):

    def setUp(self):
        build_case("R-001", DentalCase.Status.SUBMITTED)
        build_case("R-002", DentalCase.Status.IN_REVIEW)
        build_case("R-003", DentalCase.Status.IN_PROGRESS)
        build_case("R-004", DentalCase.Status.COMPLETED)
        build_case("R-005", DentalCase.Status.DELIVERED)
        build_case("R-006", DentalCase.Status.CANCELLED)

    def test_production_indicators(self):
        """
        Los indicadores cuentan cada grupo de estados correctamente.
        """

        report = ReportService.get_production_report()
        metrics = report["metrics"]

        self.assertTrue(report["has_data"])
        self.assertEqual(metrics["total"], 6)
        self.assertEqual(metrics["pending"], 2)
        self.assertEqual(metrics["in_progress"], 1)
        self.assertEqual(metrics["completed"], 2)
        self.assertEqual(metrics["cancelled"], 1)

        # 2 completados sobre 6 casos
        self.assertEqual(metrics["completion_rate"], 33.3)

    def test_average_turnaround_is_calculated(self):
        """
        El tiempo promedio mide dias reales entre creacion y cierre,
        y solo toma en cuenta los casos terminados.
        """

        DentalCase.objects.all().delete()

        ahora = timezone.now()

        # Dos casos terminados: uno de 10 dias y otro de 20.
        for numero, dias in (("T-001", 10), ("T-002", 20)):
            caso = build_case(numero, DentalCase.Status.COMPLETED)
            DentalCase.objects.filter(pk=caso.pk).update(
                created_at=ahora - timedelta(days=dias),
                updated_at=ahora,
            )

        # Un caso abierto de 90 dias, que no debe entrar en el promedio.
        abierto = build_case("T-003", DentalCase.Status.IN_PROGRESS)
        DentalCase.objects.filter(pk=abierto.pk).update(
            created_at=ahora - timedelta(days=90),
            updated_at=ahora,
        )

        report = ReportService.get_production_report()

        self.assertEqual(
            report["metrics"]["average_turnaround_days"], 15.0
        )

    def test_overdue_excludes_finished_cases(self):
        """
        Un caso vencido pero ya entregado no cuenta como vencido.
        """

        ayer = timezone.now().date() - timedelta(days=3)

        build_case("R-007", DentalCase.Status.IN_PROGRESS, due_date=ayer)
        build_case("R-008", DentalCase.Status.DELIVERED, due_date=ayer)
        build_case("R-009", DentalCase.Status.CANCELLED, due_date=ayer)

        report = ReportService.get_production_report()

        self.assertEqual(report["metrics"]["overdue"], 1)

    def test_report_without_data(self):
        """
        Sin casos, el reporte responde has_data en False y no falla.
        """

        DentalCase.objects.all().delete()

        report = ReportService.get_production_report()

        self.assertFalse(report["has_data"])
        self.assertEqual(report["metrics"]["total"], 0)
        self.assertEqual(report["metrics"]["completion_rate"], 0)

    def test_database_failure_becomes_report_error(self):
        """
        Un fallo de la capa de datos se traduce a ReportGenerationError.
        """

        with patch(
            "apps.reports.services.ReportSelector.get_filtered_cases",
            side_effect=DatabaseError("database is locked"),
        ):

            with self.assertLogs("apps.reports.services", level="ERROR"):

                with self.assertRaises(ReportGenerationError):
                    ReportService.get_production_report()


class ReportFilterTests(TestCase):

    def setUp(self):
        hoy = timezone.now()

        self.viejo = build_case(
            "F-001",
            DentalCase.Status.COMPLETED,
            created_at=hoy - timedelta(days=40),
        )
        self.reciente = build_case(
            "F-002",
            DentalCase.Status.IN_PROGRESS,
            created_at=hoy - timedelta(days=2),
        )
        self.otro = build_case(
            "F-003",
            DentalCase.Status.IN_PROGRESS,
            created_at=hoy - timedelta(days=1),
        )

        Workflow.objects.create(case_number="F-002", current_stage="QC")
        Workflow.objects.create(case_number="F-003", current_stage="DESIGN")

    def test_filter_by_period(self):
        """
        El filtro de período deja fuera los casos anteriores al rango.
        """

        desde = (timezone.now() - timedelta(days=7)).date()

        report = ReportService.get_production_report({"date_from": desde})

        self.assertEqual(report["metrics"]["total"], 2)

    def test_filter_by_status(self):
        """
        El filtro por estado devuelve solo los casos de ese estado.
        """

        report = ReportService.get_production_report(
            {"status": DentalCase.Status.COMPLETED}
        )

        self.assertEqual(report["metrics"]["total"], 1)
        self.assertEqual(report["metrics"]["completed"], 1)

    def test_filter_by_workflow_stage(self):
        """
        El filtro por etapa cruza los casos con el workflow por numero.
        """

        report = ReportService.get_production_report({"stage": "QC"})

        self.assertEqual(report["metrics"]["total"], 1)

    def test_filters_combine(self):
        """
        Los filtros se aplican juntos, no uno u otro.
        """

        desde = (timezone.now() - timedelta(days=7)).date()

        report = ReportService.get_production_report(
            {
                "date_from": desde,
                "status": DentalCase.Status.COMPLETED,
            }
        )

        self.assertEqual(report["metrics"]["total"], 0)
        self.assertFalse(report["has_data"])

    def test_form_rejects_inverted_period(self):
        """
        La fecha final no puede ser anterior a la inicial.
        """

        form = ReportFilterForm(
            {"date_from": "2026-09-10", "date_to": "2026-09-01"}
        )

        self.assertFalse(form.is_valid())
        self.assertIn("date_to", form.errors)


class CaseStatusReportTests(TestCase):

    def setUp(self):
        build_case("S-001", DentalCase.Status.IN_PROGRESS)
        build_case("S-002", DentalCase.Status.IN_PROGRESS)
        build_case("S-003", DentalCase.Status.COMPLETED)
        build_case("S-004", DentalCase.Status.SUBMITTED)

        Workflow.objects.create(case_number="S-001", current_stage="PRINTING")
        Workflow.objects.create(case_number="S-002", current_stage="PRINTING")
        Workflow.objects.create(case_number="S-003", current_stage="SHIPPED")

    def test_status_distribution_matches_stored_data(self):
        """
        La distribucion coincide con lo guardado y suma el total.
        """

        report = ReportService.get_case_status_report()

        self.assertEqual(report["total"], 4)

        por_estado = {
            row["status"]: row["total"] for row in report["by_status"]
        }

        self.assertEqual(por_estado[DentalCase.Status.IN_PROGRESS], 2)
        self.assertEqual(por_estado[DentalCase.Status.COMPLETED], 1)
        self.assertEqual(por_estado[DentalCase.Status.SUBMITTED], 1)

        self.assertEqual(
            sum(row["total"] for row in report["by_status"]),
            report["total"],
        )

    def test_percentages(self):
        """
        Los porcentajes se calculan sobre el total filtrado.
        """

        report = ReportService.get_case_status_report()

        por_estado = {
            row["status"]: row["percentage"] for row in report["by_status"]
        }

        self.assertEqual(por_estado[DentalCase.Status.IN_PROGRESS], 50.0)

    def test_stage_distribution(self):
        """
        La distribucion por etapa agrupa los workflows de esos casos.
        """

        report = ReportService.get_case_status_report()

        por_etapa = {
            row["current_stage"]: row["total"] for row in report["by_stage"]
        }

        self.assertEqual(por_etapa["PRINTING"], 2)
        self.assertEqual(por_etapa["SHIPPED"], 1)

    def test_stage_distribution_without_workflows(self):
        """
        Casos sin workflow no rompen el reporte.
        """

        Workflow.objects.all().delete()

        report = ReportService.get_case_status_report()

        self.assertTrue(report["has_data"])
        self.assertEqual(report["by_stage"], [])


class ReportViewTests(TestCase):

    def setUp(self):
        self.url = reverse("operational_reports")

        self.user = User.objects.create_user(
            username="santiago_test",
            password="clave-de-prueba",
        )

        build_case("V-001", DentalCase.Status.IN_PROGRESS)

    def test_reports_require_login(self):
        """
        Un usuario anonimo es redirigido al login.
        """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_reports_page_renders(self):
        """
        La pagina muestra los dos reportes.
        """

        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["report_error"])
        self.assertTrue(response.context["production"]["has_data"])

    def test_page_shows_message_when_reports_fail(self):
        """
        Si la generacion falla, la pagina responde 200 con un mensaje.
        """

        self.client.force_login(self.user)

        with patch(
            "apps.reports.views.ReportService.get_production_report",
            side_effect=ReportGenerationError("boom"),
        ):

            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["report_error"],
            OperationalReportsView.REPORT_ERROR_MESSAGE,
        )

    def test_csv_download(self):
        """
        La descarga devuelve un CSV con los datos del reporte.
        """

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("download_report", args=["production"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])

        contenido = response.content.decode()

        self.assertIn("Production performance report", contenido)
        self.assertIn("Total cases", contenido)

    def test_download_without_data_informs_the_user(self):
        """
        Sin datos no se entrega un CSV vacio, se explica el motivo.
        """

        self.client.force_login(self.user)

        DentalCase.objects.all().delete()

        response = self.client.get(
            reverse("download_report", args=["production"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            "no data available",
            response.content.decode(),
        )

    def test_unknown_report_type(self):
        """
        Un tipo de reporte inexistente responde 404, no un error.
        """

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("download_report", args=["inventado"])
        )

        self.assertEqual(response.status_code, 404)
