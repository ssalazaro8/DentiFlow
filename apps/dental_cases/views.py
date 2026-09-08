from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .exceptions import DashboardMetricsError
from .services import DentalCaseService

from .forms import (
    DentalCaseCreateForm,
    DentalCaseUpdateForm,
)


def dental_case_list(request):
    """
    Displays all dental cases.
    """

    dental_cases = DentalCaseService.get_all()

    return render(
        request,
        "dental_cases/list.html",
        {
            "dental_cases": dental_cases,
        },
    )


def dental_case_create(request):
    """
    Creates a new dental work order.
    """

    if request.method == "POST":

        form = DentalCaseCreateForm(
            request.POST
        )

        if form.is_valid():

            dental_case = DentalCaseService.create(
                form.cleaned_data
            )

            messages.success(
                request,
                (
                    f"Dental case "
                    f"{dental_case.case_number} "
                    "was created successfully."
                ),
            )

            return redirect(
                "dental_case_detail",
                case_id=dental_case.id,
            )

    else:

        form = DentalCaseCreateForm()

    return render(
        request,
        "dental_cases/create.html",
        {
            "form": form,
        },
    )


def dental_case_detail(request, case_id):
    """
    Displays a dental case and its related files.
    """

    dental_case = DentalCaseService.get_by_id(
        case_id
    )

    if dental_case is None:

        messages.error(
            request,
            "Dental case not found.",
        )

        return redirect(
            "dental_case_list"
        )

    case_files = dental_case.files.all()

    return render(
        request,
        "dental_cases/detail.html",
        {
            "dental_case": dental_case,
            "case_files": case_files,
        },
    )


def dental_case_edit(request, case_id):
    """
    Updates an existing dental case.
    """

    dental_case = DentalCaseService.get_by_id(
        case_id
    )

    if dental_case is None:

        messages.error(
            request,
            "Dental case not found.",
        )

        return redirect(
            "dental_case_list"
        )

    if request.method == "POST":

        form = DentalCaseUpdateForm(
            request.POST,
            instance=dental_case,
        )

        if form.is_valid():

            try:

                DentalCaseService.update(
                    dental_case,
                    form.cleaned_data,
                )

            except ValueError as error:

                form.add_error(
                    "status",
                    str(error),
                )

            else:

                messages.success(
                    request,
                    (
                        f"Dental case "
                        f"{dental_case.case_number} "
                        "was updated successfully."
                    ),
                )

                return redirect(
                    "dental_case_detail",
                    case_id=dental_case.id,
                )

    else:

        form = DentalCaseUpdateForm(
            instance=dental_case,
        )

    return render(
        request,
        "dental_cases/edit.html",
        {
            "form": form,
            "dental_case": dental_case,
        },
    )


def dental_case_delete(request, case_id):
    """
    Deletes an existing dental case.
    """

    dental_case = DentalCaseService.get_by_id(
        case_id
    )

    if dental_case is None:

        messages.error(
            request,
            "Dental case not found.",
        )

        return redirect(
            "dental_case_list"
        )

    if request.method == "POST":

        case_number = dental_case.case_number

        DentalCaseService.delete(
            dental_case
        )

        messages.success(
            request,
            (
                f"Dental case "
                f"{case_number} "
                "was deleted successfully."
            ),
        )

        return redirect(
            "dental_case_list"
        )

    return render(
        request,
        "dental_cases/confirm_delete.html",
        {
            "dental_case": dental_case,
        },
    )

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Displays the real time production indicators of the laboratory.
    """

    template_name = "dental_cases/dashboard.html"

    METRICS_ERROR_MESSAGE = (
        "The production indicators could not be loaded. "
        "Please try again in a few moments."
    )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        try:

            metrics = DentalCaseService.get_dashboard_metrics()

        except DashboardMetricsError:

            # The dashboard keeps rendering, but the cards are
            # replaced by an explanatory message.
            context.update(
                {
                    "metrics_error": self.METRICS_ERROR_MESSAGE,
                    "pending": None,
                    "in_progress": None,
                    "completed": None,
                    "total_active": None,
                    "cases_by_stage": [],
                }
            )

        else:

            context.update(
                {
                    "metrics_error": None,
                    "pending": metrics["pending"],
                    "in_progress": metrics["in_progress"],
                    "completed": metrics["completed"],
                    "total_active": metrics["total_active"],
                    "cases_by_stage": metrics["cases_by_stage"],
                }
            )

        return context