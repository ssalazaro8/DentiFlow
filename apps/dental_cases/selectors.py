from .models import DentalCase


class DentalCaseSelector:

    @staticmethod
    def get_all():
        """
        Returns all dental cases ordered by creation date.
        """
        return DentalCase.objects.all()

    @staticmethod
    def get_by_id(case_id):
        """
        Returns a dental case by its ID.
        """
        return DentalCase.objects.filter(id=case_id).first()

    @staticmethod
    def get_by_case_number(case_number):
        """
        Returns a dental case by its case number.
        """
        return DentalCase.objects.filter(case_number=case_number).first()