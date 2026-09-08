from django.db.models import Avg, Count, F, Q
from django.utils import timezone

from apps.dental_cases.models import DentalCase
from apps.workflow.models import Workflow


class ReportSelector:
    """
    Read-only queries that feed the operational reports.

    Every query starts from the same filtered queryset, so the
    production report and the case status report always describe
    the same set of cases.
    """

    COMPLETED_STATUSES = [
        DentalCase.Status.COMPLETED,
        DentalCase.Status.DELIVERED,
    ]

    PENDING_STATUSES = [
        DentalCase.Status.SUBMITTED,
        DentalCase.Status.IN_REVIEW,
    ]

    # A case that is finished or cancelled can no longer be overdue.
    CLOSED_STATUSES = COMPLETED_STATUSES + [DentalCase.Status.CANCELLED]

    @staticmethod
    def get_filtered_cases(
        date_from=None,
        date_to=None,
        status=None,
        stage=None,
        laboratory=None,
    ):
        """
        Returns the dental cases matching the report filters.
        """

        cases = DentalCase.objects.all()

        if date_from:
            cases = cases.filter(created_at__date__gte=date_from)

        if date_to:
            cases = cases.filter(created_at__date__lte=date_to)

        if status:
            cases = cases.filter(status=status)

        if stage:
            # Workflow references the case by its number instead of a
            # foreign key, so the stage filter has to go through the
            # case numbers currently sitting in that stage.
            case_numbers = Workflow.objects.filter(
                current_stage=stage
            ).values_list("case_number", flat=True)

            cases = cases.filter(case_number__in=case_numbers)

        if laboratory:
            # Placeholder for the laboratory scope. DentalCase has no
            # laboratory relation yet (it arrives with PR #31), so the
            # filter is accepted and ignored on purpose instead of
            # silently returning every laboratory's cases as if it had
            # been applied.
            pass

        return cases

    @staticmethod
    def get_production_metrics(cases):
        """
        Returns the production performance indicators for a queryset.
        """

        total = cases.count()

        completed = cases.filter(
            status__in=ReportSelector.COMPLETED_STATUSES
        ).count()

        in_progress = cases.filter(
            status=DentalCase.Status.IN_PROGRESS
        ).count()

        pending = cases.filter(
            status__in=ReportSelector.PENDING_STATUSES
        ).count()

        cancelled = cases.filter(
            status=DentalCase.Status.CANCELLED
        ).count()

        overdue = cases.filter(
            due_date__lt=timezone.now().date()
        ).exclude(
            status__in=ReportSelector.CLOSED_STATUSES
        ).count()

        # Turnaround is measured only on finished cases: an open case
        # has not spent its full time in the laboratory yet.
        turnaround = cases.filter(
            status__in=ReportSelector.COMPLETED_STATUSES
        ).aggregate(
            average=Avg(F("updated_at") - F("created_at"))
        )["average"]

        average_days = None

        if turnaround is not None:
            average_days = round(turnaround.total_seconds() / 86400, 1)

        by_service = list(
            cases.values("service_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        service_labels = dict(DentalCase.SERVICE_TYPES)

        for row in by_service:
            row["label"] = service_labels.get(
                row["service_type"],
                row["service_type"],
            )

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "cancelled": cancelled,
            "overdue": overdue,
            "completion_rate": (
                round(completed * 100 / total, 1) if total else 0
            ),
            "average_turnaround_days": average_days,
            "by_service": by_service,
        }

    @staticmethod
    def get_status_distribution(cases):
        """
        Returns how the cases are distributed across their statuses.
        """

        total = cases.count()

        rows = list(
            cases.values("status")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        status_labels = dict(DentalCase.Status.choices)

        for row in rows:
            row["label"] = status_labels.get(row["status"], row["status"])
            row["percentage"] = (
                round(row["total"] * 100 / total, 1) if total else 0
            )

        return rows

    @staticmethod
    def get_stage_distribution(cases):
        """
        Returns how the cases are distributed across workflow stages.
        """

        case_numbers = list(cases.values_list("case_number", flat=True))

        if not case_numbers:
            return []

        rows = list(
            Workflow.objects.filter(case_number__in=case_numbers)
            .values("current_stage")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        stage_labels = dict(Workflow.STAGE_CHOICES)

        for row in rows:
            row["label"] = stage_labels.get(
                row["current_stage"],
                row["current_stage"],
            )

        return rows
