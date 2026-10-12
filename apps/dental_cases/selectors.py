from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .models import DentalCase, DentalCaseFile
from .permissions import filter_accessible_cases


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

    @staticmethod
    def get_visible_to(user):
        """
        Returns the dental cases the user is allowed to see.
        """
        return filter_accessible_cases(
            user,
            DentalCaseSelector.get_all(),
        )

    @staticmethod
    def search(cases, term):
        """
        Narrows a queryset to the cases whose number, clinic or
        requester contains the term, ignoring upper and lower case.
        """
        return cases.filter(
            Q(case_number__icontains=term)
            | Q(clinic_name__icontains=term)
            | Q(requested_by__icontains=term)
        )

    @staticmethod
    def filter_by(
        cases,
        status=None,
        service_type=None,
        due_from=None,
        due_to=None,
    ):
        """
        Narrows a queryset by status, service type and due date range.
        """

        if status:
            cases = cases.filter(status=status)

        if service_type:
            cases = cases.filter(service_type=service_type)

        if due_from:
            cases = cases.filter(due_date__gte=due_from)

        if due_to:
            cases = cases.filter(due_date__lte=due_to)

        return cases

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
        
        # Agrupa y cuenta los casos por cada estado existente.
        # Se agrega la etiqueta legible para no mostrar el valor crudo
        # de la base ("IN_PROGRESS") en la pantalla.
        cases_by_stage = list(
            base_qs.values('status').annotate(total=Count('id'))
        )

        status_labels = dict(DentalCase.Status.choices)

        for row in cases_by_stage:
            row['label'] = status_labels.get(row['status'], row['status'])
        
        return {
            'pending': pending_cases,
            'in_progress': in_progress_cases,
            'completed': completed_cases,
            'total_active': pending_cases + in_progress_cases,
            'cases_by_stage': cases_by_stage
        }


# --- FR-24: acceso a los archivos adjuntos del caso ---

def get_case_file_by_id(*, file_id: int) -> DentalCaseFile:
    return get_object_or_404(DentalCaseFile, id=file_id)
