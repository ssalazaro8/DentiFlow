import logging

from django.db import transaction

from .exceptions import DashboardMetricsError
from .models import DentalCase
from .selectors import DentalCaseSelector

logger = logging.getLogger(__name__)


class DentalCaseService:

    STATUS_TRANSITIONS = {
        DentalCase.Status.SUBMITTED: {
            DentalCase.Status.IN_REVIEW,
            DentalCase.Status.CANCELLED,
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
    @transaction.atomic
    def create(data):
        """
        Creates a new dental case.

        Every new case starts in SUBMITTED status.
        """

        data = data.copy()

        data["status"] = DentalCase.Status.SUBMITTED

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

        case.status = new_status

        case.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return case

    @staticmethod
    @transaction.atomic
    def delete(case):
        """
        Deletes an existing dental case.
        """

        case.delete()