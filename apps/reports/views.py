from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from apps.laboratories.models import Laboratory

from .exceptions import ReportGenerationError
from .forms import ReportFilterForm
from .services import ReportService


def get_allowed_laboratories(user):
    """
    Returns the laboratories whose cases the user may see in a report.

    Superusers get None, meaning no restriction. Everyone else is
    limited to the laboratories they are authorised for, so a user
    with no laboratory sees an empty report instead of somebody
    else's production data.
    """

    if user.is_superuser:
        return None

    return Laboratory.objects.filter(authorized_users=user)


class OperationalReportsView(LoginRequiredMixin, TemplateView):
    """
    Lets the user request and view the operational reports.
    """

    template_name = "reports/operational_reports.html"

    REPORT_ERROR_MESSAGE = (
        "The reports could not be generated. "
        "Please try again in a few moments."
    )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        form = ReportFilterForm(self.request.GET or None)
        filters = form.as_filters()
        filters["laboratories"] = get_allowed_laboratories(self.request.user)

        context["form"] = form

        try:

            context["production"] = ReportService.get_production_report(
                filters
            )
            context["status_report"] = ReportService.get_case_status_report(
                filters
            )
            context["report_error"] = None

        except ReportGenerationError:

            # The page keeps rendering, with a message in place of
            # the report tables.
            context["production"] = None
            context["status_report"] = None
            context["report_error"] = self.REPORT_ERROR_MESSAGE

        return context


@login_required
def download_report_view(request, report_type):
    """
    Downloads an operational report as a CSV file.
    """

    form = ReportFilterForm(request.GET or None)
    filters = form.as_filters()
    filters["laboratories"] = get_allowed_laboratories(request.user)

    builders = {
        "production": (
            ReportService.get_production_report,
            ReportService.write_production_csv,
        ),
        "status": (
            ReportService.get_case_status_report,
            ReportService.write_case_status_csv,
        ),
    }

    if report_type not in builders:

        return render(
            request,
            "reports/report_error.html",
            {"message": "The requested report does not exist."},
            status=404,
        )

    build, write_csv = builders[report_type]

    try:

        report = build(filters)

    except ReportGenerationError as error:

        return render(
            request,
            "reports/report_error.html",
            {"message": str(error)},
            status=500,
        )

    if not report["has_data"]:

        # Nothing to download is not a failure, but handing over an
        # empty file would look like one.
        return render(
            request,
            "reports/report_error.html",
            {
                "message": (
                    "There is no data available to generate this "
                    "report with the selected filters."
                )
            },
            status=200,
        )

    filename = (
        f"{report_type}_report_"
        f"{timezone.now().date().isoformat()}.csv"
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    write_csv(report, response)

    return response
