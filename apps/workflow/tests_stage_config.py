"""
FR-23: configuración de etapas de producción por laboratorio.

Cada laboratorio arma su propia secuencia, y la configuración de uno
nunca alcanza a la de otro.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.laboratories.models import Laboratory

from .models import WorkflowStage
from .services import WorkflowStageService


class WorkflowStageConfigTests(TestCase):

    def setUp(self):
        self.lab_a = Laboratory.objects.create(
            name="Lab A", email="a@stages.com", phone="1",
            city="Medellin", address="Calle 1", service="CROWN",
        )
        self.lab_b = Laboratory.objects.create(
            name="Lab B", email="b@stages.com", phone="2",
            city="Bogota", address="Calle 2", service="BRIDGE",
        )

        self.gerente_a = get_user_model().objects.create_user(
            "gerente_a", password="clave"
        )
        self.lab_a.authorized_users.add(self.gerente_a)

        self.gerente_b = get_user_model().objects.create_user(
            "gerente_b", password="clave"
        )
        self.lab_b.authorized_users.add(self.gerente_b)

        for nombre in ("Recepcion", "Diseno", "Fresado"):
            WorkflowStageService.create(self.lab_a, nombre)

    def nombres(self, laboratory, only_active=False):
        return [
            e.name
            for e in WorkflowStageService.get_stages(
                laboratory, only_active=only_active
            )
        ]

    # --- Creación y configuración ---

    def test_manager_creates_stages_in_sequence(self):
        """
        Las etapas se crean una detras de otra, numeradas.
        """

        etapas = WorkflowStageService.get_stages(self.lab_a)

        self.assertEqual(
            [e.name for e in etapas], ["Recepcion", "Diseno", "Fresado"]
        )
        self.assertEqual([e.order for e in etapas], [1, 2, 3])

    def test_stage_belongs_to_a_single_laboratory(self):
        etapa = WorkflowStageService.get_stages(self.lab_a).first()

        self.assertEqual(etapa.laboratory, self.lab_a)

    def test_duplicate_stage_name_is_rejected(self):
        """
        No puede haber dos etapas con el mismo nombre en un laboratorio,
        ni cambiando mayusculas o espacios.
        """

        with self.assertRaises(ValueError):
            WorkflowStageService.create(self.lab_a, "Diseno")

        with self.assertRaises(ValueError):
            WorkflowStageService.create(self.lab_a, "  diseno  ")

    def test_empty_stage_name_is_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowStageService.create(self.lab_a, "   ")

    def test_stage_can_be_renamed(self):
        etapa = WorkflowStageService.get_stages(self.lab_a).first()

        WorkflowStageService.update(etapa, name="Recepcion de caso")
        etapa.refresh_from_db()

        self.assertEqual(etapa.name, "Recepcion de caso")

    def test_renaming_onto_an_existing_name_is_rejected(self):
        etapa = WorkflowStageService.get_stages(self.lab_a).first()

        with self.assertRaises(ValueError):
            WorkflowStageService.update(etapa, name="Fresado")

    # --- Activación ---

    def test_stage_can_be_deactivated_and_reactivated(self):
        etapa = WorkflowStageService.get_stages(self.lab_a).first()

        WorkflowStageService.toggle_active(etapa)
        etapa.refresh_from_db()
        self.assertFalse(etapa.is_active)

        WorkflowStageService.toggle_active(etapa)
        etapa.refresh_from_db()
        self.assertTrue(etapa.is_active)

    def test_inactive_stages_are_left_out_when_asked(self):
        etapa = WorkflowStageService.get_stages(self.lab_a).first()
        WorkflowStageService.toggle_active(etapa)

        self.assertEqual(
            self.nombres(self.lab_a, only_active=True),
            ["Diseno", "Fresado"],
        )
        # Pero siguen existiendo en la configuracion.
        self.assertEqual(len(self.nombres(self.lab_a)), 3)

    # --- Orden ---

    def test_stage_moves_down_and_up(self):
        """
        Mover una etapa intercambia su posicion con la vecina.
        """

        recepcion = WorkflowStageService.get_stages(self.lab_a).first()

        WorkflowStageService.move(recepcion, "down")
        self.assertEqual(
            self.nombres(self.lab_a), ["Diseno", "Recepcion", "Fresado"]
        )

        WorkflowStageService.move(recepcion, "up")
        self.assertEqual(
            self.nombres(self.lab_a), ["Recepcion", "Diseno", "Fresado"]
        )

    def test_moving_beyond_the_edge_does_nothing(self):
        """
        La primera no sube y la ultima no baja, y no se rompe.
        """

        etapas = list(WorkflowStageService.get_stages(self.lab_a))

        WorkflowStageService.move(etapas[0], "up")
        WorkflowStageService.move(etapas[-1], "down")

        self.assertEqual(
            self.nombres(self.lab_a), ["Recepcion", "Diseno", "Fresado"]
        )

    def test_invalid_direction_is_rejected(self):
        etapa = WorkflowStageService.get_stages(self.lab_a).first()

        with self.assertRaises(ValueError):
            WorkflowStageService.move(etapa, "sideways")

    # --- Aislamiento entre laboratorios ---

    def test_same_stage_name_allowed_in_another_laboratory(self):
        """
        Dos laboratorios pueden llamar igual a sus etapas.
        """

        etapa = WorkflowStageService.create(self.lab_b, "Diseno")

        self.assertEqual(etapa.laboratory, self.lab_b)
        self.assertEqual(
            WorkflowStage.objects.filter(name="Diseno").count(), 2
        )

    def test_configuring_one_laboratory_does_not_touch_the_other(self):
        """
        Crear, mover y desactivar en A deja intacta la secuencia de B.
        """

        for nombre in ("Entrada", "Control"):
            WorkflowStageService.create(self.lab_b, nombre)

        antes = [
            (e.name, e.order, e.is_active)
            for e in WorkflowStageService.get_stages(self.lab_b)
        ]

        etapas_a = list(WorkflowStageService.get_stages(self.lab_a))
        WorkflowStageService.move(etapas_a[0], "down")
        WorkflowStageService.toggle_active(etapas_a[1])
        WorkflowStageService.create(self.lab_a, "Empaque")

        despues = [
            (e.name, e.order, e.is_active)
            for e in WorkflowStageService.get_stages(self.lab_b)
        ]

        self.assertEqual(antes, despues)

    def test_query_never_returns_another_laboratory(self):
        WorkflowStageService.create(self.lab_b, "Entrada")

        etapas_a = WorkflowStageService.get_stages(self.lab_a)

        self.assertTrue(all(e.laboratory == self.lab_a for e in etapas_a))

    # --- Acceso desde la interfaz ---

    def test_manager_sees_the_configuration_in_order(self):
        self.client.force_login(self.gerente_a)

        response = self.client.get(
            reverse("workflow_stage_list", args=[self.lab_a.id])
        )
        contenido = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            contenido.index("Recepcion"), contenido.index("Diseno")
        )
        self.assertLess(
            contenido.index("Diseno"), contenido.index("Fresado")
        )

    def test_manager_cannot_see_another_laboratory_configuration(self):
        """
        El gerente de B no llega a la configuracion de A.
        """

        self.client.force_login(self.gerente_b)

        response = self.client.get(
            reverse("workflow_stage_list", args=[self.lab_a.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_cannot_modify_another_laboratory_configuration(self):
        self.client.force_login(self.gerente_b)

        response = self.client.post(
            reverse("workflow_stage_create", args=[self.lab_a.id]),
            {"name": "Intrusa", "is_active": "on"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            WorkflowStage.objects.filter(name="Intrusa").exists()
        )

    def test_anonymous_cannot_reach_the_configuration(self):
        response = self.client.get(
            reverse("workflow_stage_list", args=[self.lab_a.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_full_configuration_flow_from_the_interface(self):
        """
        Flujo completo: crear una etapa, subirla, desactivarla, y
        comprobar que la secuencia quedo como se configuro.
        """

        self.client.force_login(self.gerente_a)

        self.client.post(
            reverse("workflow_stage_create", args=[self.lab_a.id]),
            {"name": "Empaque", "is_active": "on"},
        )

        empaque = WorkflowStage.objects.get(
            laboratory=self.lab_a, name="Empaque"
        )

        self.client.post(
            reverse(
                "workflow_stage_move",
                args=[self.lab_a.id, empaque.id, "up"],
            )
        )

        self.client.post(
            reverse(
                "workflow_stage_toggle", args=[self.lab_a.id, empaque.id]
            )
        )

        empaque.refresh_from_db()

        self.assertEqual(empaque.order, 3)
        self.assertFalse(empaque.is_active)
        self.assertEqual(
            self.nombres(self.lab_a),
            ["Recepcion", "Diseno", "Empaque", "Fresado"],
        )
