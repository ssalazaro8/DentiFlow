from django.shortcuts import get_object_or_404

from .models import DentalCase, DentalCaseFile


class DentalCaseSelector:

    @staticmethod
    def get_all():
        """
        Returns all dental cases.
        """
        return DentalCase.objects.all()

    @staticmethod
    def get_by_id(case_id):
        """
        Returns a dental case by primary key.
        """
        return DentalCase.objects.filter(
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


# --- FR-24: acceso a los archivos adjuntos del caso ---

def get_case_file_by_id(*, file_id: int) -> DentalCaseFile:
    return get_object_or_404(DentalCaseFile, id=file_id)
