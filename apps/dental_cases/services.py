from .models import DentalCase
from .selectors import DentalCaseSelector


class DentalCaseService:

    @staticmethod
    def get_all():
        return DentalCaseSelector.get_all()

    @staticmethod
    def get_by_id(case_id):
        return DentalCaseSelector.get_by_id(case_id)

    @staticmethod
    def create(data):
        return DentalCase.objects.create(**data)