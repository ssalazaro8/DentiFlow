import logging
from datetime import timedelta

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
    def get_dashboard_metrics():
        """
        Returns the production indicators of the laboratory.

        Any failure while calculating the indicators is logged and
        translated into a DashboardMetricsError, so the view can
        show a message instead of returning a broken page.
        """

        try:

            return DentalCaseSelector.get_dashboard_metrics()

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
    def get_technician_workload(laboratory):
        """
        FR-29: active and recently completed cases of each technician.
        """
        since = timezone.now() - timedelta(days=30)
        finished = [DentalCase.Status.DELIVERED, DentalCase.Status.CANCELLED, DentalCase.Status.REJECTED]
        rows = []
        for technician in laboratory.technicians.order_by("first_name", "last_name", "username"):
            assignments = TechnicianAssignment.objects.filter(technician=technician)
            cases = []
            for assignment in assignments.select_related("dental_case__workflow").order_by("-assigned_at"):
                workflow = getattr(assignment.dental_case, "workflow", None)
                cases.append({
                    "case": assignment.dental_case,
                    "stage": workflow.get_current_stage_display() if workflow else "Not started",
                    "progress": workflow.progress_percentage if workflow else 0,
                })
            # shortcut: updated_at stands in for the completion date, add a completed_at field for an exact count
            rows.append({
                "technician": technician,
                "cases": cases,
                "active": assignments.exclude(dental_case__status__in=finished).count(),
                "completed_30d": assignments.filter(
                    dental_case__status__in=[DentalCase.Status.COMPLETED, DentalCase.Status.DELIVERED],
                    dental_case__updated_at__gte=since,
                ).count(),
            })
        busiest = max((row["active"] for row in rows), default=0)
        for row in rows:
            row["idle"] = row["active"] == 0
            row["busiest"] = busiest > 0 and row["active"] == busiest
        return rows

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