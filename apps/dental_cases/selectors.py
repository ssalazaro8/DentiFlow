from .models import DentalCase


class DentalCaseSelector:

    @staticmethod
    def get_all():
        """
        Returns all dental cases.
        """
        return DentalCase.objects.select_related("laboratory").prefetch_related("technician_assignment__technician")

    @staticmethod
    def get_by_id(case_id):
        """
        Returns a dental case by primary key.
        """
        return DentalCase.objects.select_related("laboratory").prefetch_related("technician_assignment__technician").filter(
            id=case_id
        ).first()

    @staticmethod
    def get_by_case_number(case_number):
        """
        Returns a dental case by case number.
        """
        return DentalCase.objects.filter(
            case_number=case_number
        ).first()

    @staticmethod
    def get_by_status(status):
        """
        Returns all cases with a specific status.
        """
        return DentalCase.objects.filter(
            status=status
        )

    @staticmethod
    def get_by_clinic(clinic_name):
        """
        Returns all cases belonging to a clinic.
        """
        return DentalCase.objects.filter(
            clinic_name__iexact=clinic_name
        )
