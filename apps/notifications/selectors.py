from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Notification


class NotificationSelector:

    @staticmethod
    def for_user(user):
        return (
            Notification.objects
            .filter(recipient=user)
            .select_related("dental_case", "material")
        )

    @staticmethod
    def pending_for_user(user):
        return NotificationSelector.for_user(user).filter(is_read=False)

    @staticmethod
    def read_for_user(user):
        return NotificationSelector.for_user(user).filter(is_read=True)

    @staticmethod
    def unread_count(user):
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @staticmethod
    def case_recipients(case):
        """
        Usuarios involucrados en un caso: quien lo creo, el tecnico
        asignado y el personal del laboratorio destino.
        """

        User = get_user_model()
        involved = Q()

        if case.created_by_id:
            involved |= Q(pk=case.created_by_id)

        assignment = getattr(case, "technician_assignment", None)
        if assignment is not None:
            involved |= Q(pk=assignment.technician_id)

        if case.laboratory_id:
            involved |= Q(authorized_laboratories=case.laboratory_id)
            involved |= Q(technician_laboratories=case.laboratory_id)

        if not involved:
            return User.objects.none()

        return User.objects.filter(involved, is_active=True).distinct()

    @staticmethod
    def stock_alert_recipients():
        """
        El material no pertenece a un laboratorio: se avisa a los tecnicos
        y usuarios autorizados de los laboratorios y a los superusuarios.
        """

        User = get_user_model()

        return User.objects.filter(
            Q(is_superuser=True)
            | Q(authorized_laboratories__isnull=False)
            | Q(technician_laboratories__isnull=False),
            is_active=True,
        ).distinct()