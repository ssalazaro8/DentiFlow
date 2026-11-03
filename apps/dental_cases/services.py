import calendar
import logging
from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.notifications.services import NotificationService

from .exceptions import DashboardMetricsError
from .models import DentalCase, TechnicianAssignment, DeliveryRegistration
from .selectors import DentalCaseSelector

logger = logging.getLogger(__name__)


class DentalCaseService:

    STATUS_TRANSITIONS = {
        DentalCase.Status.SUBMITTED: {
            DentalCase.Status.IN_PROGRESS,
            DentalCase.Status.CANCELLED,
            DentalCase.Status.REJECTED,
        },

        DentalCase.Status.IN_REVIEW: {
            DentalCase.Status.IN_PROGRESS,
            DentalCase.Status.CANCELLED,
        },

        DentalCase.Status.IN_PROGRESS: {
            DentalCase.Status.COMPLETED,
            DentalCase.Status.CANCELLED,
        },

        DentalCase.Status.COMPLETED: {
            DentalCase.Status.DELIVERED,
        },

        DentalCase.Status.DELIVERED: set(),

        DentalCase.Status.CANCELLED: set(),
        DentalCase.Status.REJECTED: set(),
    }

    @staticmethod
    def get_dashboard_metrics(cases=None):
        """
        Returns the production indicators of the laboratory.

        Any failure while calculating the indicators is logged and
        translated into a DashboardMetricsError, so the view can
        show a message instead of returning a broken page.
        """

        try:

            return DentalCaseSelector.get_dashboard_metrics(cases)

        except Exception as error:

            logger.exception(
                "Failed to calculate the dashboard metrics."
            )

            raise DashboardMetricsError(
                "The production indicators could not be loaded."
            ) from error

    @staticmethod
    def get_all():
        return DentalCaseSelector.get_all()

    @staticmethod
    def get_by_id(case_id):
        return DentalCaseSelector.get_by_id(case_id)

    @staticmethod
    def get_by_case_number(case_number):
        return DentalCaseSelector.get_by_case_number(
            case_number
        )

    @staticmethod
    def get_by_status(status):
        return DentalCaseSelector.get_by_status(
            status
        )

    @staticmethod
    def get_by_clinic(clinic_name):
        return DentalCaseSelector.get_by_clinic(
            clinic_name
        )

    @staticmethod
    def get_visible_cases(user):
        return DentalCaseSelector.get_visible_to(user)

    @staticmethod
    def filter_cases(cases, filters=None):
        """
        Applies the search term and the list filters to a queryset.
        """

        filters = filters or {}

        if filters.get("q"):
            cases = DentalCaseSelector.search(
                cases,
                filters["q"],
            )

        return DentalCaseSelector.filter_by(
            cases,
            status=filters.get("status"),
            service_type=filters.get("service_type"),
            due_from=filters.get("due_from"),
            due_to=filters.get("due_to"),
        )

    @staticmethod
    @transaction.atomic
    def create(data, created_by=None):
        """
        Creates a new dental case.

        Every new case starts in SUBMITTED status.
        """

        data = data.copy()

        data["status"] = DentalCase.Status.SUBMITTED
        if data.get("clinic"):
            data["clinic_name"] = data["clinic"].name
        if created_by is not None:
            data["created_by"] = created_by

        return DentalCase.objects.create(
            **data
        )

    @staticmethod
    @transaction.atomic
    def update(case, data):
        """
        Updates the editable information of a dental case.
        """

        data = data.copy()

        requested_status = data.pop(
            "status",
            case.status,
        )

        if requested_status != case.status:

            DentalCaseService.update_status(
                case,
                requested_status,
            )

        for field, value in data.items():
            setattr(
                case,
                field,
                value,
            )

        case.save()

        return case

    @staticmethod
    @transaction.atomic
    def update_status(case, new_status):
        """
        Changes the lifecycle status of a dental case.

        Only valid lifecycle transitions are allowed.
        """

        if new_status == case.status:
            return case

        allowed_statuses = (
            DentalCaseService.STATUS_TRANSITIONS.get(
                case.status,
                set(),
            )
        )

        if new_status not in allowed_statuses:

            raise ValueError(
                (
                    f"Invalid status transition: "
                    f"{case.status} -> {new_status}"
                )
            )

        previous_label = case.get_status_display()

        case.status = new_status

        case.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # FR-12: avisa a los usuarios involucrados del nuevo estado.
        NotificationService.notify_case_status_change(case, previous_label)

        return case

    @staticmethod
    @transaction.atomic
    def accept(case):
        if case.acceptance_status != DentalCase.AcceptanceStatus.PENDING:
            raise ValueError("This case has already received a laboratory decision.")
        case.acceptance_status = DentalCase.AcceptanceStatus.ACCEPTED
        case.accepted_at = timezone.now()
        case.rejection_reason = ""
        case.save(update_fields=["acceptance_status", "accepted_at", "rejection_reason", "updated_at"])
        return case

    @staticmethod
    @transaction.atomic
    def reject(case, reason):
        if case.acceptance_status != DentalCase.AcceptanceStatus.PENDING:
            raise ValueError("This case has already received a laboratory decision.")
        if not reason or not reason.strip():
            raise ValueError("A reason is required to reject a dental case.")
        previous_label = case.get_status_display()
        case.acceptance_status = DentalCase.AcceptanceStatus.REJECTED
        case.rejection_reason = reason.strip()
        case.rejected_at = timezone.now()
        case.status = DentalCase.Status.REJECTED
        case.save(update_fields=["acceptance_status", "rejection_reason", "rejected_at", "status", "updated_at"])

        # FR-12: el rechazo tambien cambia el estado del caso.
        NotificationService.notify_case_status_change(case, previous_label)
        return case

    @staticmethod
    @transaction.atomic
    def assign_technician(case, technician):
        if case.acceptance_status != DentalCase.AcceptanceStatus.ACCEPTED:
            raise ValueError("Only an accepted case can be assigned to a technician.")
        if not case.laboratory or not case.laboratory.technicians.filter(pk=technician.pk).exists():
            raise ValueError("The selected technician does not belong to this laboratory.")
        assignment, _ = TechnicianAssignment.objects.update_or_create(
            dental_case=case,
            defaults={"technician": technician},
        )
        return assignment

    @staticmethod
    @transaction.atomic
    def remove_technician_assignment(case):
        TechnicianAssignment.objects.filter(dental_case=case).delete()

    @staticmethod
    @transaction.atomic
    def start_production(case):
        if case.acceptance_status != DentalCase.AcceptanceStatus.ACCEPTED:
            raise ValueError("Production can only begin after laboratory acceptance.")
        if not hasattr(case, "technician_assignment"):
            raise ValueError("Assign a technician before starting production.")
        if case.status == DentalCase.Status.SUBMITTED:
            return DentalCaseService.update_status(case, DentalCase.Status.IN_PROGRESS)
        return case

    @staticmethod
    @transaction.atomic
    def delete(case):
        """
        Deletes an existing dental case.
        """

        case.delete()

    @staticmethod
    @transaction.atomic
    def mark_as_completed(case):
        """
        FR-27: marks a case as completed.
        Changes the status to COMPLETED.
        """
        if case.status != DentalCase.Status.IN_PROGRESS:
            raise ValueError("Only in-progress cases can be marked as completed.")

        return DentalCaseService.update_status(case, DentalCase.Status.COMPLETED)

    @staticmethod
    @transaction.atomic
    def register_delivery(case, destination_clinic, registered_by, notes=""):
        """
        FR-27: registers the delivery of a completed case.
        Changes the status to DELIVERED and creates the delivery record.
        """
        if case.status != DentalCase.Status.COMPLETED:
            raise ValueError("Only completed cases can be delivered.")

        DentalCaseService.update_status(case, DentalCase.Status.DELIVERED)

        delivery = DeliveryRegistration.objects.create(
            dental_case=case,
            destination_clinic=destination_clinic,
            registered_by=registered_by,
            notes=notes,
            completed_at=timezone.now(),
        )

        return delivery


# --- FR-34: delivery calendar ---

OVERDUE = "overdue"
DELIVERED = "delivered"
UPCOMING = "upcoming"


def parse_month(value, today):
    """
    Returns the first day of a month written as YYYY-MM, or of the
    current month when the value is missing or not valid.
    """

    try:
        year, month = (int(part) for part in value.split("-"))
        return date(year, month, 1)
    except (AttributeError, TypeError, ValueError):
        return today.replace(day=1)


def _shift_month(first_day, months):

    index = first_day.year * 12 + first_day.month - 1 + months

    return date(index // 12, index % 12 + 1, 1)


def delivery_state(dental_case, today):
    """
    Delivered cases are done; the rest are overdue once their due date
    has passed.
    """

    if dental_case.status == DentalCase.Status.DELIVERED:
        return DELIVERED

    if dental_case.due_date < today:
        return OVERDUE

    return UPCOMING


class DeliveryCalendarService:
    """
    Places the visible cases of a month on their due date (FR-34).
    """

    @staticmethod
    def build(cases, month=None, today=None):

        today = today or timezone.localdate()
        first_day = month or today.replace(day=1)

        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(
            first_day.year, first_day.month
        )

        due = DentalCaseSelector.get_due_between(cases, weeks[0][0], weeks[-1][-1])

        by_day = {}
        totals = {OVERDUE: 0, DELIVERED: 0, UPCOMING: 0}

        for dental_case in due:

            state = delivery_state(dental_case, today)
            by_day.setdefault(dental_case.due_date, []).append(
                {"case": dental_case, "state": state}
            )

            if dental_case.due_date.month == first_day.month:
                totals[state] += 1

        return {
            "month": first_day,
            "previous_month": _shift_month(first_day, -1).strftime("%Y-%m"),
            "next_month": _shift_month(first_day, 1).strftime("%Y-%m"),
            "current_month": today.strftime("%Y-%m"),
            "is_current_month": first_day == today.replace(day=1),
            "weeks": [
                [
                    {
                        "date": day,
                        "in_month": day.month == first_day.month,
                        "is_today": day == today,
                        "cases": by_day.get(day, []),
                    }
                    for day in week
                ]
                for week in weeks
            ],
            "totals": totals,
            "total": sum(totals.values()),
        }
