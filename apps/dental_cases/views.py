from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from .forms import (
    DentalCaseCreateForm,
    DentalCaseUpdateForm,
)
from .selectors import get_case_file_by_id
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


# --- FR-24: descarga de archivos adjuntos ---


@login_required
def download_case_file_view(request, file_id: int):
    case_file = get_case_file_by_id(file_id=file_id)

    if not case_file.file or not case_file.file.storage.exists(case_file.file.name):
        raise Http404("El archivo solicitado no existe en el servidor.")

    return FileResponse(
        case_file.file.open("rb"),
        as_attachment=True,
        filename=case_file.filename,
    )
