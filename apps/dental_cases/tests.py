from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.laboratories.models import Laboratory
from .models import DentalCase
from .services import DentalCaseService


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
