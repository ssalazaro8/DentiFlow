from .models import DentalCase
from django.db.models import Count


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

    @staticmethod
    def get_dashboard_metrics():

        base_qs = DentalCase.objects.all()
        
        pending_cases = base_qs.filter(
            status__in=[DentalCase.Status.SUBMITTED, DentalCase.Status.IN_REVIEW]
        ).count()
        
        in_progress_cases = base_qs.filter(
            status=DentalCase.Status.IN_PROGRESS
        ).count()
        
        completed_cases = base_qs.filter(
            status__in=[DentalCase.Status.COMPLETED, DentalCase.Status.DELIVERED]
        ).count()
        
        # Agrupa y cuenta los casos por cada estado existente
        cases_by_stage = base_qs.values('status').annotate(total=Count('id'))
        
        return {
            'pending': pending_cases,
            'in_progress': in_progress_cases,
            'completed': completed_cases,
            'total_active': pending_cases + in_progress_cases,
            'cases_by_stage': list(cases_by_stage)
        }