import csv
import logging

from datetime import timedelta

from django.utils import timezone

from .exceptions import ReportGenerationError
from .selectors import AnalyticsSelector, ReportSelector

logger = logging.getLogger(__name__)


class ReportService:
    """
    Builds the operational reports requested from the interface.
    """

    @staticmethod
    def get_production_report(filters=None):
        """
        Returns the production performance report.

        An empty result is not an error: it comes back with
        has_data set to False so the view can tell the user that
        there is nothing to report for those filters.
        """

        filters = filters or {}

        try:

            cases = ReportSelector.get_filtered_cases(**filters)

            metrics = ReportSelector.get_production_metrics(cases)

        except Exception as error:

            logger.exception(
                "Failed to generate the production report."
            )

            raise ReportGenerationError(
                "The production report could not be generated."
            ) from error

        return {
            "has_data": metrics["total"] > 0,
            "metrics": metrics,
        }

    @staticmethod
    def get_case_status_report(filters=None):
        """
        Returns the case status report.
        """

        filters = filters or {}

        try:

            cases = ReportSelector.get_filtered_cases(**filters)

            by_status = ReportSelector.get_status_distribution(cases)
            by_stage = ReportSelector.get_stage_distribution(cases)
            total = cases.count()

        except Exception as error:

            logger.exception(
                "Failed to generate the case status report."
            )

            raise ReportGenerationError(
                "The case status report could not be generated."
            ) from error

        return {
            "has_data": total > 0,
            "total": total,
            "by_status": by_status,
            "by_stage": by_stage,
        }

    @staticmethod
    def write_production_csv(report, output):
        """
        Writes the production report into a CSV stream.
        """

        metrics = report["metrics"]
        writer = csv.writer(output)

        writer.writerow(["Production performance report"])
        writer.writerow([])

        writer.writerow(["Indicator", "Value"])
        writer.writerow(["Total cases", metrics["total"]])
        writer.writerow(["Completed", metrics["completed"]])
        writer.writerow(["In progress", metrics["in_progress"]])
        writer.writerow(["Pending", metrics["pending"]])
        writer.writerow(["Cancelled", metrics["cancelled"]])
        writer.writerow(["Rejected", metrics["rejected"]])
        writer.writerow(["Overdue", metrics["overdue"]])
        writer.writerow(["Completion rate (%)", metrics["completion_rate"]])
        writer.writerow(
            [
                "Average turnaround (days)",
                metrics["average_turnaround_days"]
                if metrics["average_turnaround_days"] is not None
                else "N/A",
            ]
        )

        writer.writerow([])
        writer.writerow(["Service type", "Cases"])

        for row in metrics["by_service"]:
            writer.writerow([row["label"], row["total"]])

        return output

    @staticmethod
    def write_case_status_csv(report, output):
        """
        Writes the case status report into a CSV stream.
        """

        writer = csv.writer(output)

        writer.writerow(["Case status report"])
        writer.writerow([])

        writer.writerow(["Status", "Cases", "Percentage"])

        for row in report["by_status"]:
            writer.writerow([row["label"], row["total"], row["percentage"]])

        writer.writerow([])
        writer.writerow(["Workflow stage", "Cases"])

        for row in report["by_stage"]:
            writer.writerow([row["label"], row["total"]])

        return output


# --- FR-14: laboratory analytics ---

WEEK = "week"
MONTH = "month"
PERIODS = (WEEK, MONTH)

# How many periods the charts show, counting the current one.
PERIODS_SHOWN = 12


def _local_date(moment):
    return timezone.localtime(moment).date()


def period_start(day, period):
    """
    Returns the first day of the week (Monday) or month of a date.
    """

    if period == MONTH:
        return day.replace(day=1)

    return day - timedelta(days=day.weekday())


def _previous_start(start, period):

    if period == MONTH:
        return (start - timedelta(days=1)).replace(day=1)

    return start - timedelta(days=7)


def period_starts(today, period, count=PERIODS_SHOWN):
    """
    Returns the first day of the last periods, oldest first.
    """

    starts = [period_start(today, period)]

    while len(starts) < count:
        starts.append(_previous_start(starts[-1], period))

    return list(reversed(starts))


def period_label(start, period):

    if period == MONTH:
        return start.strftime("%b %Y")

    return start.strftime("%b %d")


def _average(values):

    if not values:
        return None

    return round(sum(values) / len(values), 1)


class AnalyticsService:
    """
    Computes the laboratory analytics (FR-14).
    """

    @staticmethod
    def build(laboratories=None, period=WEEK, today=None):
        """
        Returns the indicators of each period and a summary of them.

        - Case volume: cases received, by the day they were created.
        - Average production time: days from the acceptance of a case
          (or its creation, when it was never accepted) to its delivery,
          by the day it was delivered.
        - On time delivery: share of the deliveries made on or before
          the due date, by the day they were delivered.
        """

        if period not in PERIODS:
            period = WEEK

        today = today or timezone.localdate()
        starts = period_starts(today, period)
        first_day = starts[0]

        received = {start: 0 for start in starts}
        production_days = {start: [] for start in starts}
        on_time = {start: [] for start in starts}

        for case in AnalyticsSelector.get_cases(laboratories):

            created = _local_date(case.created_at)

            if created >= first_day:
                received[period_start(created, period)] += 1

            delivery = getattr(case, "delivery_registration", None)

            if delivery is None:
                continue

            delivered = _local_date(delivery.delivered_at)

            if delivered < first_day:
                continue

            start = period_start(delivered, period)
            began = case.accepted_at or case.created_at
            elapsed = delivery.delivered_at - began

            production_days[start].append(elapsed.total_seconds() / 86400)
            on_time[start].append(delivered <= case.due_date)

        rows = []

        for start in starts:

            deliveries = on_time[start]

            rows.append(
                {
                    "label": period_label(start, period),
                    "cases": received[start],
                    "deliveries": len(deliveries),
                    "average_days": _average(production_days[start]),
                    "on_time_rate": (
                        round(100 * sum(deliveries) / len(deliveries), 1)
                        if deliveries
                        else None
                    ),
                }
            )

        all_days = [value for values in production_days.values() for value in values]
        all_deliveries = [value for values in on_time.values() for value in values]

        summary = {
            "cases": sum(received.values()),
            "deliveries": len(all_deliveries),
            "average_days": _average(all_days),
            "on_time_rate": (
                round(100 * sum(all_deliveries) / len(all_deliveries), 1)
                if all_deliveries
                else None
            ),
        }

        return {
            "period": period,
            "rows": rows,
            "summary": summary,
            "has_cases": summary["cases"] > 0,
            "has_deliveries": summary["deliveries"] > 0,
            "chart": {
                "labels": [row["label"] for row in rows],
                "cases": [row["cases"] for row in rows],
                "average_days": [row["average_days"] for row in rows],
                "on_time_rate": [row["on_time_rate"] for row in rows],
            },
        }
