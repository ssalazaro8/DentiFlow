from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Workflow, CaseStatusHistory
from .services import WorkflowService


User = get_user_model()


class CaseStatusHistoryTests(TestCase):

    def setUp(self):
        # Crear usuario responsable de los cambios
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword"
        )

        # Crear un caso dental
        self.workflow = Workflow.objects.create(
            case_number="CASE-001",
            current_stage="RECEIVED",
            comments="Test case"
        )

    def test_status_change_creates_history(self):
        """
        Verifica que al cambiar el estado
        se cree automáticamente un registro histórico.
        """

        WorkflowService.update_stage(
            self.workflow,
            "DESIGN",
            self.user
        )

        history = CaseStatusHistory.objects.filter(
            workflow=self.workflow
        )

        self.assertEqual(history.count(), 1)

    def test_history_stores_previous_and_new_status(self):
        """
        Verifica que el historial almacene
        correctamente el estado anterior y el nuevo.
        """

        WorkflowService.update_stage(
            self.workflow,
            "DESIGN",
            self.user
        )

        history = CaseStatusHistory.objects.get(
            workflow=self.workflow
        )

        self.assertEqual(
            history.previous_status,
            "RECEIVED"
        )

        self.assertEqual(
            history.new_status,
            "DESIGN"
        )

    def test_history_stores_responsible_user(self):
        """
        Verifica que el historial almacene
        el usuario responsable del cambio.
        """

        WorkflowService.update_stage(
            self.workflow,
            "DESIGN",
            self.user
        )

        history = CaseStatusHistory.objects.get(
            workflow=self.workflow
        )

        self.assertEqual(
            history.changed_by,
            self.user
        )

    def test_history_has_automatic_timestamp(self):
        """
        Verifica que el timestamp se genere automáticamente.
        """

        WorkflowService.update_stage(
            self.workflow,
            "DESIGN",
            self.user
        )

        history = CaseStatusHistory.objects.get(
            workflow=self.workflow
        )

        self.assertIsNotNone(
            history.timestamp
        )

    def test_multiple_status_changes_create_complete_history(self):
        """
        Verifica que varios cambios de estado
        generen varios registros históricos.
        """

        WorkflowService.update_stage(
            self.workflow,
            "DESIGN",
            self.user
        )

        WorkflowService.update_stage(
            self.workflow,
            "PRINTING",
            self.user
        )

        WorkflowService.update_stage(
            self.workflow,
            "QC",
            self.user
        )

        history = CaseStatusHistory.objects.filter(
            workflow=self.workflow
        ).order_by("timestamp")

        self.assertEqual(
            history.count(),
            3
        )

        self.assertEqual(
            history[0].previous_status,
            "RECEIVED"
        )

        self.assertEqual(
            history[0].new_status,
            "DESIGN"
        )

        self.assertEqual(
            history[1].previous_status,
            "DESIGN"
        )

        self.assertEqual(
            history[1].new_status,
            "PRINTING"
        )

        self.assertEqual(
            history[2].previous_status,
            "PRINTING"
        )

        self.assertEqual(
            history[2].new_status,
            "QC"
        )

    def test_same_status_does_not_create_history(self):
        """
        Verifica que no se cree un historial
        cuando el estado no cambia.
        """

        WorkflowService.update_stage(
            self.workflow,
            "RECEIVED",
            self.user
        )

        history = CaseStatusHistory.objects.filter(
            workflow=self.workflow
        )

        self.assertEqual(
            history.count(),
            0
        )

    def test_history_is_preserved_after_new_status_change(self):
        """
        Verifica que los registros históricos anteriores
        no sean modificados cuando ocurre un nuevo cambio.
        """

        WorkflowService.update_stage(
            self.workflow,
            "DESIGN",
            self.user
        )

        first_history = CaseStatusHistory.objects.get(
            workflow=self.workflow
        )

        first_previous_status = first_history.previous_status
        first_new_status = first_history.new_status

        WorkflowService.update_stage(
            self.workflow,
            "PRINTING",
            self.user
        )

        first_history.refresh_from_db()

        self.assertEqual(
            first_history.previous_status,
            first_previous_status
        )

        self.assertEqual(
            first_history.new_status,
            first_new_status
        )