from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.dental_cases.models import DentalCase
from apps.dental_cases.services import DentalCaseService
from apps.laboratories.models import Laboratory
from .services import WorkflowService


class CaseTrackingTests(TestCase):
    def test_tracking_update_is_saved_in_history(self):
        laboratory = Laboratory.objects.create(
            name="Lab", email="tracking@example.com", phone="1", city="Medellin",
            address="Street 1", service="CROWN",
        )
        technician = get_user_model().objects.create_user("tracking-tech")
        laboratory.technicians.add(technician)
        dental_case = DentalCase.objects.create(
            case_number="DF-101", clinic_name="Clinic", requested_by="Dr. Test",
            laboratory=laboratory, service_type="CROWN", description="Case", due_date=date.today(),
        )
        DentalCaseService.accept(dental_case)
        DentalCaseService.assign_technician(dental_case, technician)
        DentalCaseService.start_production(dental_case)
        workflow = WorkflowService.create({"dental_case": dental_case, "current_stage": "RECEIVED", "comments": "", "progress_percentage": 0})
        WorkflowService.update_stage(workflow, "DESIGN", 25, "Design started", technician)
        workflow.refresh_from_db()
        self.assertEqual(workflow.current_stage, "DESIGN")
        self.assertEqual(workflow.progress_percentage, 25)
        self.assertEqual(workflow.updates.count(), 2)


class CaseStatusHistoryTests(TestCase):
    """
    FR-22: cada cambio de etapa queda registrado con su etapa anterior,
    su responsable y su fecha, en un historial completo y ordenado.
    """

    def setUp(self):
        self.laboratory = Laboratory.objects.create(
            name="Lab Historial",
            email="historial@example.com",
            phone="1",
            city="Medellin",
            address="Calle 1",
            service="CROWN",
        )

        self.tecnico = get_user_model().objects.create_user(
            "tecnico_historial", password="clave"
        )
        self.laboratory.authorized_users.add(self.tecnico)
        self.laboratory.technicians.add(self.tecnico)

        self.intruso = get_user_model().objects.create_user(
            "intruso_historial", password="clave"
        )

        self.case = DentalCase.objects.create(
            case_number="HIST-001",
            clinic_name="Clinica",
            requested_by="Dr. Test",
            laboratory=self.laboratory,
            service_type="CROWN",
            description="Caso con historial",
            due_date=date.today(),
        )
        DentalCaseService.accept(self.case)

        self.workflow = WorkflowService.create(
            {"dental_case": self.case, "current_stage": "RECEIVED"}
        )

    def avanzar(self, etapa, porcentaje, comentario="", user=None):
        return WorkflowService.update_stage(
            self.workflow,
            etapa,
            porcentaje,
            comentario,
            user=user or self.tecnico,
        )

    def test_every_change_is_recorded(self):
        """
        Cada cambio de etapa genera un registro nuevo.
        """

        # El primero lo crea el propio workflow.
        self.assertEqual(self.workflow.updates.count(), 1)

        self.avanzar("DESIGN", 25)
        self.avanzar("PRINTING", 50)

        self.assertEqual(self.workflow.updates.count(), 3)

    def test_previous_and_new_stage_are_stored(self):
        """
        El registro guarda de donde venia y hacia donde fue.
        """

        self.avanzar("DESIGN", 25)

        registro = self.workflow.updates.first()

        self.assertEqual(registro.previous_stage, "RECEIVED")
        self.assertEqual(registro.stage, "DESIGN")

    def test_first_record_has_no_previous_stage(self):
        """
        El registro inicial no tiene etapa anterior, y no inventa una.
        """

        primero = self.workflow.updates.last()

        self.assertEqual(primero.previous_stage, "")
        self.assertEqual(primero.stage, "RECEIVED")

    def test_responsible_user_is_stored(self):
        """
        El historial guarda quien hizo el cambio.
        """

        self.avanzar("DESIGN", 25)

        self.assertEqual(
            self.workflow.updates.first().updated_by, self.tecnico
        )

    def test_timestamp_is_automatic(self):
        """
        La fecha y hora se registran solas.
        """

        self.avanzar("DESIGN", 25)

        self.assertIsNotNone(self.workflow.updates.first().created_at)

    def test_history_is_ordered_and_complete(self):
        """
        El historial va del cambio mas reciente al mas antiguo y no
        pierde ninguno.
        """

        self.avanzar("DESIGN", 25)
        self.avanzar("PRINTING", 50)
        self.avanzar("QC", 75)

        etapas = list(
            self.workflow.updates.values_list("stage", flat=True)
        )

        self.assertEqual(etapas, ["QC", "PRINTING", "DESIGN", "RECEIVED"])

    def test_existing_records_are_not_modified(self):
        """
        Un cambio nuevo no altera los registros anteriores.
        """

        self.avanzar("DESIGN", 25, "primer avance")

        primero = self.workflow.updates.first()
        antes = (primero.pk, primero.stage, primero.comment)

        self.avanzar("PRINTING", 50, "segundo avance")

        primero.refresh_from_db()

        self.assertEqual(
            (primero.pk, primero.stage, primero.comment), antes
        )

    def test_authorized_user_can_see_the_history_page(self):
        """
        Un usuario del laboratorio abre el historial del caso.
        """

        self.avanzar("DESIGN", 25)

        self.client.force_login(self.tecnico)

        response = self.client.get(
            reverse("workflow_history", args=[self.workflow.id])
        )

        contenido = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("HIST-001", contenido)
        self.assertIn("3D Design", contenido)
        self.assertIn("Received", contenido)

    def test_unrelated_user_cannot_see_the_history(self):
        """
        El historial respeta el mismo control de acceso que el caso.
        """

        self.client.force_login(self.intruso)

        response = self.client.get(
            reverse("workflow_history", args=[self.workflow.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_see_the_history(self):
        response = self.client.get(
            reverse("workflow_history", args=[self.workflow.id])
        )

        self.assertEqual(response.status_code, 302)
