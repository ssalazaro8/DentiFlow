from django.db import transaction
from django.utils import timezone

from .models import DentalCase, TechnicianAssignment
from .selectors import DentalCaseSelector


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
        case.acceptance_status = DentalCase.AcceptanceStatus.REJECTED
        case.rejection_reason = reason.strip()
        case.rejected_at = timezone.now()
        case.status = DentalCase.Status.REJECTED
        case.save(update_fields=["acceptance_status", "rejection_reason", "rejected_at", "status", "updated_at"])
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
