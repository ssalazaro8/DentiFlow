import csv
import logging

from .exceptions import ReportGenerationError
from .selectors import ReportSelector

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
