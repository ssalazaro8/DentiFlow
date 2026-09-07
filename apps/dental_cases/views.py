from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.laboratories.models import Laboratory
from apps.clinics.models import Clinic

from .forms import (
    DentalCaseCreateForm,
    DentalCaseUpdateForm,
    RejectionForm,
    TechnicianAssignmentForm,
)
from .services import DentalCaseService


def _require_laboratory_access(request, dental_case):
    """Allows the laboratory's authorised users (or superusers) to act."""
    laboratory = dental_case.laboratory
    if not laboratory:
        raise PermissionDenied("You are not authorized to manage this laboratory case.")


def _can_view_case(user, dental_case):
    if not user.is_authenticated:
        return False
    if user.is_superuser or dental_case.created_by_id == user.id:
        return True
    return bool(
        dental_case.laboratory
        and dental_case.laboratory.authorized_users.filter(pk=user.pk).exists()
    )


def dental_case_list(request):
    """
    Displays all dental cases.
    """

    # There is no role-aware identity yet, so do not expose an all-cases list.
    # Users enter through a selected clinic or laboratory inbox instead.
    return redirect("dental_case_create")


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
                form.cleaned_data,
                created_by=request.user if request.user.is_authenticated else None,
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
    assignment = getattr(dental_case, "technician_assignment", None)
    workflow = getattr(dental_case, "workflow", None)
    # Temporary demo mode: roles are not implemented yet, so the selected
    # laboratory can operate the case through its own inbox.
    can_manage_laboratory = dental_case.laboratory is not None

    return render(
        request,
        "dental_cases/detail.html",
        {
            "dental_case": dental_case,
            "case_files": case_files,
            "assignment": assignment,
            "workflow": workflow,
            "can_manage_laboratory": can_manage_laboratory,
        },
    )


def laboratory_case_inbox(request, laboratory_id):
    """Private inbox of proposals sent to one laboratory."""
    laboratory = get_object_or_404(Laboratory, pk=laboratory_id)
    dental_cases = DentalCaseService.get_all().filter(laboratory=laboratory)
    return render(request, "dental_cases/list.html", {"dental_cases": dental_cases, "laboratory": laboratory})


def clinic_case_inbox(request, clinic_id):
    """Temporary clinic-side inbox until identity and roles are enabled."""
    clinic = get_object_or_404(Clinic, pk=clinic_id)
    dental_cases = DentalCaseService.get_all().filter(clinic=clinic)
    return render(request, "dental_cases/list.html", {"dental_cases": dental_cases, "clinic": clinic})


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

    if not _can_view_case(request.user, dental_case):
        raise PermissionDenied("You are not authorized to edit this dental case.")

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

    if not _can_view_case(request.user, dental_case):
        raise PermissionDenied("You are not authorized to delete this dental case.")

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


def dental_case_accept(request, case_id):
    dental_case = DentalCaseService.get_by_id(case_id)
    if not dental_case:
        messages.error(request, "Dental case not found.")
        return redirect("dental_case_list")
    _require_laboratory_access(request, dental_case)
    if request.method != "POST":
        return redirect("dental_case_detail", case_id=case_id)
    try:
        DentalCaseService.accept(dental_case)
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Dental case accepted. You can now assign a technician.")
    return redirect("dental_case_detail", case_id=case_id)


def dental_case_reject(request, case_id):
    dental_case = DentalCaseService.get_by_id(case_id)
    if not dental_case:
        messages.error(request, "Dental case not found.")
        return redirect("dental_case_list")
    _require_laboratory_access(request, dental_case)
    form = RejectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            DentalCaseService.reject(dental_case, form.cleaned_data["reason"])
        except ValueError as error:
            form.add_error("reason", str(error))
        else:
            messages.success(request, "Dental case rejected and the reason was recorded.")
            return redirect("dental_case_detail", case_id=case_id)
    return render(request, "dental_cases/reject.html", {"dental_case": dental_case, "form": form})


def technician_assignment(request, case_id):
    dental_case = DentalCaseService.get_by_id(case_id)
    if not dental_case:
        messages.error(request, "Dental case not found.")
        return redirect("dental_case_list")
    _require_laboratory_access(request, dental_case)
    current_assignment = getattr(dental_case, "technician_assignment", None)
    form = TechnicianAssignmentForm(request.POST or None, laboratory=dental_case.laboratory)
    if request.method == "POST" and form.is_valid():
        try:
            assignment = DentalCaseService.assign_technician(dental_case, form.cleaned_data["technician"])
        except ValueError as error:
            form.add_error("technician", str(error))
        else:
            verb = "updated" if current_assignment else "assigned"
            messages.success(request, f"Technician {assignment.technician} {verb} successfully.")
            return redirect("dental_case_detail", case_id=case_id)
    return render(request, "dental_cases/assign_technician.html", {"dental_case": dental_case, "form": form, "assignment": current_assignment})


def technician_assignment_remove(request, case_id):
    dental_case = DentalCaseService.get_by_id(case_id)
    if not dental_case:
        messages.error(request, "Dental case not found.")
        return redirect("dental_case_list")
    _require_laboratory_access(request, dental_case)
    if request.method == "POST":
        DentalCaseService.remove_technician_assignment(dental_case)
        messages.success(request, "Technician assignment removed.")
    return redirect("dental_case_detail", case_id=case_id)
