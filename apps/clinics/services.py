from .models import Clinic
from .selectors import ClinicSelector


class ClinicService:

    @staticmethod
    def get_all():

        return ClinicSelector.get_all()

    @staticmethod
    def get_by_id(clinic_id):

        return ClinicSelector.get_by_id(
            clinic_id
        )

    @staticmethod
    def create(data):

        return Clinic.objects.create(
            **data
        )