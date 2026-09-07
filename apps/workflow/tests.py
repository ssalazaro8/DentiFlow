from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

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
