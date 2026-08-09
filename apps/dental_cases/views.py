from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import (
    DentalCaseCreateForm,
    DentalCaseUpdateForm,
)
from .models import DentalCase
from .services import DentalCaseService


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
                    f"was created successfully."
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
    Displays a dental case.
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

    return render(
        request,
        "dental_cases/detail.html",
        {
            "dental_case": dental_case,
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
                        f"was updated successfully."
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
                f"was deleted successfully."
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