from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.dental_cases.models import DentalCase

from .forms import CaseFileUploadForm
from .models import CaseFile
from .selectors import CaseFileSelector
from .services import CaseFileService


def case_file_list(
    request,
    case_id,
):
    """
    Displays all files belonging
    to a dental case.
    """

    dental_case = get_object_or_404(
        DentalCase,
        id=case_id,
    )

    files = (
        CaseFileSelector.get_by_case(
            dental_case
        )
    )

    return render(
        request,
        "documents/list.html",
        {
            "dental_case": dental_case,
            "files": files,
        },
    )


def case_file_upload(
    request,
    case_id,
):
    """
    Uploads one or multiple files
    to a dental case.
    """

    dental_case = get_object_or_404(
        DentalCase,
        id=case_id,
    )

    if request.method == "POST":

        form = CaseFileUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            files = (
                form.cleaned_data[
                    "files"
                ]
            )

            category = (
                form.cleaned_data[
                    "category"
                ]
            )

            CaseFileService.create_multiple(
                dental_case=dental_case,
                category=category,
                uploaded_files=files,
            )

            messages.success(
                request,
                (
                    f"{len(files)} file(s) "
                    "uploaded successfully."
                ),
            )

            return redirect(
                "dental_case_detail",
                case_id=dental_case.id,
            )

    else:

        form = CaseFileUploadForm()

    return render(
        request,
        "documents/upload.html",
        {
            "form": form,
            "dental_case": dental_case,
        },
    )


def case_file_delete(
    request,
    case_id,
    file_id,
):
    """
    Deletes a file associated
    with a dental case.
    """

    dental_case = get_object_or_404(
        DentalCase,
        id=case_id,
    )

    case_file = get_object_or_404(
        CaseFile,
        id=file_id,
        dental_case=dental_case,
    )

    if request.method == "POST":

        file_name = (
            case_file.original_name
        )

        CaseFileService.delete(
            case_file
        )

        messages.success(
            request,
            (
                f"{file_name} "
                "was deleted successfully."
            ),
        )

        return redirect(
            "dental_case_detail",
            case_id=dental_case.id,
        )

    return render(
        request,
        "documents/confirm_delete.html",
        {
            "dental_case": dental_case,
            "case_file": case_file,
        },
    )


def case_file_download(
    request,
    case_id,
    file_id,
):
    """
    Downloads a case file.
    """

    dental_case = get_object_or_404(
        DentalCase,
        id=case_id,
    )

    case_file = get_object_or_404(
        CaseFile,
        id=file_id,
        dental_case=dental_case,
    )

    if not case_file.file:

        raise Http404(
            "The requested file does not exist."
        )

    return FileResponse(
        case_file.file.open(
            "rb"
        ),
        as_attachment=True,
        filename=case_file.original_name,
    )
