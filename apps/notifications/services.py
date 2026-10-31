from django.utils import timezone

from .models import Notification
from .selectors import NotificationSelector


class NotificationService:
    """FR-12: crea los avisos y los marca como leidos."""

    @staticmethod
    def notify(recipients, *, kind, message, dental_case=None, material=None):
        notifications = [
            Notification(
                recipient=user,
                kind=kind,
                message=message,
                dental_case=dental_case,
                material=material,
            )
            for user in recipients
        ]
        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def notify_case_status_change(case, previous_label):
        message = (
            f"Case {case.case_number} changed status from "
            f"{previous_label} to {case.get_status_display()}."
        )
        return NotificationService.notify(
            NotificationSelector.case_recipients(case),
            kind=Notification.Kind.CASE_STATUS,
            message=message,
            dental_case=case,
        )

    @staticmethod
    def notify_stock_alert(alert):
        material = alert.material
        message = (
            f"Low stock alert: {material.name} has "
            f"{alert.stock_when_opened} {material.get_unit_type_display()} left "
            f"(minimum {alert.reorder_level_when_opened})."
        )
        return NotificationService.notify(
            NotificationSelector.stock_alert_recipients(),
            kind=Notification.Kind.STOCK_ALERT,
            message=message,
            material=material,
        )

    @staticmethod
    def mark_as_read(notification):
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return notification

    @staticmethod
    def mark_all_as_read(user):
        return Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())