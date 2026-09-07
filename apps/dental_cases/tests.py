from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import DentalCase
from .services import DentalCaseService

class DashboardMetricsTests(TestCase):
    def setUp(self):
        self.test_user = "santiago_test"
        
        # Datos base para no repetir en cada creación
        base_data = {
            "clinic_name": "Clinica Prueba",
            "requested_by": self.test_user,
            "service_type": "CROWN",
            "description": "Prueba de dashboard",
            "due_date": timezone.now().date() + timedelta(days=7)
        }

        # Creamos 2 casos pendientes
        DentalCase.objects.create(case_number="CASE-001", status=DentalCase.Status.SUBMITTED, **base_data)
        DentalCase.objects.create(case_number="CASE-002", status=DentalCase.Status.IN_REVIEW, **base_data)
        
        # Creamos 1 caso en proceso
        DentalCase.objects.create(case_number="CASE-003", status=DentalCase.Status.IN_PROGRESS, **base_data)
        
        # Creamos 1 caso completado
        DentalCase.objects.create(case_number="CASE-004", status=DentalCase.Status.COMPLETED, **base_data)
        
        # Creamos 1 caso de OTRO usuario para probar el aislamiento
        other_user_data = base_data.copy()
        other_user_data["requested_by"] = "otro_usuario"
        DentalCase.objects.create(case_number="CASE-005", status=DentalCase.Status.SUBMITTED, **other_user_data)

    def test_dashboard_metrics_calculation(self):
        """Verifica que los cálculos cuenten los estados correctamente aislando por usuario"""
        metrics = DentalCaseService.get_dashboard_metrics(self.test_user)
        
        self.assertEqual(metrics["pending"], 2)
        self.assertEqual(metrics["in_progress"], 1)
        self.assertEqual(metrics["completed"], 1)
        self.assertEqual(metrics["total_active"], 3)
        
        # Verifica que el caso del 'otro_usuario' no se haya contado
        total_cases_counted = metrics["pending"] + metrics["in_progress"] + metrics["completed"]
        self.assertEqual(total_cases_counted, 4)