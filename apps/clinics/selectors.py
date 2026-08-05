from .models import Clinic


class ClinicSelector:

    @staticmethod
    def get_all():

        return Clinic.objects.filter(
            is_active=True
        )

    @staticmethod
    def get_by_id(clinic_id):

        return Clinic.objects.filter(
            id=clinic_id
        ).first()