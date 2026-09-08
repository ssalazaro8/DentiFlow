from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.dental_cases.models import DentalCase
from apps.dental_cases.permissions import require_case_access
from apps.laboratories.models import Laboratory
from apps.laboratories.permissions import require_laboratory_access
from apps.dental_cases.services import DentalCaseService
from apps.dental_cases.views import _can_view_case
from .forms import WorkflowForm, WorkflowStageForm, WorkflowUpdateForm
from .models import Workflow, WorkflowUpdate
from .selectors import WorkflowStageSelector
from .services import WorkflowService, WorkflowStageService


def workflow_list(request):

    case_number = request.GET.get("case_number", "").strip()

    if case_number:
        workflows = WorkflowService.get_by_case(case_number)
    else:
        workflows = WorkflowService.get_all()

    return render(
        request,
        "workflow/list.html",
        {
            "workflows": workflows,
            "case_number": case_number
        }
    )

def workflow_create(request):

    if request.method == "POST":
        form = WorkflowForm(request.POST)

        if form.is_valid():
            dental_case = form.cleaned_data["dental_case"]
            try:
                WorkflowService.create(form.cleaned_data)
            except ValueError as error:
                form.add_error("dental_case", str(error))
            else:
                messages.success(request, "Production workflow started.")
                return redirect("workflow_list")

    else:
        form = WorkflowForm()

    return render(
        request,
        "workflow/create.html",
        {
            "form": form
        }
    )


def workflow_update_stage(request, id):

    workflow = WorkflowService.get_by_id(id)

    form = WorkflowUpdateForm(request.POST or None, initial={
        "current_stage": workflow.current_stage,
        "progress_percentage": workflow.progress_percentage,
        "comment": workflow.comments,
    })
    if request.method == "POST" and form.is_valid():
        try:
            WorkflowService.update_stage(
                workflow,
                stage=form.cleaned_data["current_stage"],
                progress_percentage=form.cleaned_data["progress_percentage"],
                comment=form.cleaned_data["comment"],
                user=request.user,
            )
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, "Case tracking was updated.")
            return redirect("case_tracking", case_id=workflow.dental_case.id)

    return render(
        request,
        "workflow/update.html",
        {
            "workflow": workflow,
            "form": form,
        }
    )


def case_tracking(request, case_id):
    dental_case = get_object_or_404(DentalCase, pk=case_id)
    workflow = getattr(dental_case, "workflow", None)
    return render(request, "workflow/tracking.html", {"dental_case": dental_case, "workflow": workflow})


def start_production(request, case_id):
    dental_case = get_object_or_404(DentalCase, pk=case_id)
    if request.method == "POST":
        try:
            DentalCaseService.start_production(dental_case)
            workflow, created = Workflow.objects.get_or_create(
                dental_case=dental_case,
                defaults={"current_stage": "RECEIVED", "progress_percentage": 0},
            )
            if created:
                WorkflowUpdate.objects.create(
                    workflow=workflow,
                    stage=workflow.current_stage,
                    progress_percentage=workflow.progress_percentage,
                    comment="Production workflow started.",
                    updated_by=request.user if request.user.is_authenticated else None,
                )
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, "Production started." if created else "Production was already started.")
    return redirect("case_tracking", case_id=case_id)


@login_required
def workflow_history(request, id):
    """
    FR-22: shows the complete ordered history of a case's stage changes.
    """

    workflow = WorkflowService.get_by_id(id)

    require_case_access(request.user, workflow.dental_case)

    return render(
        request,
        "workflow/history.html",
        {
            "workflow": workflow,
            "history": WorkflowService.get_status_history(workflow),
        },
    )


# --- FR-23: configuracion de etapas por laboratorio ---


def _get_laboratory_for(request, laboratory_id):
    """
    Returns the laboratory only if the user may manage it.
    """

    laboratory = get_object_or_404(Laboratory, id=laboratory_id)

    require_laboratory_access(request.user, laboratory)

    return laboratory


@login_required
def workflow_stage_list(request, laboratory_id):
    """
    Shows the stages of a laboratory in its configured order.
    """

    laboratory = _get_laboratory_for(request, laboratory_id)

    return render(
        request,
        "workflow/stages.html",
        {
            "laboratory": laboratory,
            "stages": WorkflowStageService.get_stages(laboratory),
            "form": WorkflowStageForm(),
        },
    )


@login_required
def workflow_stage_create(request, laboratory_id):
    """
    Adds a stage at the end of the laboratory's sequence.
    """

    laboratory = _get_laboratory_for(request, laboratory_id)

    if request.method == "POST":
        form = WorkflowStageForm(request.POST)

        if form.is_valid():
            try:
                WorkflowStageService.create(
                    laboratory,
                    form.cleaned_data["name"],
                    is_active=form.cleaned_data["is_active"],
                )
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, "Stage created successfully.")
        else:
            messages.error(request, "Please correct the errors in the form.")

    return redirect("workflow_stage_list", laboratory_id=laboratory.id)


@login_required
def workflow_stage_edit(request, laboratory_id, stage_id):
    """
    Renames a stage or changes whether it is active.
    """

    laboratory = _get_laboratory_for(request, laboratory_id)

    stage = WorkflowStageSelector.get_by_id(laboratory, stage_id)

    if stage is None:
        messages.error(request, "Stage not found in this laboratory.")
        return redirect("workflow_stage_list", laboratory_id=laboratory.id)

    if request.method == "POST":
        form = WorkflowStageForm(request.POST)

        if form.is_valid():
            try:
                WorkflowStageService.update(
                    stage,
                    name=form.cleaned_data["name"],
                    is_active=form.cleaned_data["is_active"],
                )
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, "Stage updated successfully.")
                return redirect(
                    "workflow_stage_list", laboratory_id=laboratory.id
                )
    else:
        form = WorkflowStageForm(
            initial={"name": stage.name, "is_active": stage.is_active}
        )

    return render(
        request,
        "workflow/stage_edit.html",
        {"laboratory": laboratory, "stage": stage, "form": form},
    )


@login_required
def workflow_stage_toggle(request, laboratory_id, stage_id):
    """
    Activates or deactivates a stage.
    """

    laboratory = _get_laboratory_for(request, laboratory_id)

    stage = WorkflowStageSelector.get_by_id(laboratory, stage_id)

    if stage is None:
        messages.error(request, "Stage not found in this laboratory.")
    elif request.method == "POST":
        WorkflowStageService.toggle_active(stage)
        estado = "activated" if stage.is_active else "deactivated"
        messages.success(request, f"Stage {estado} successfully.")

    return redirect("workflow_stage_list", laboratory_id=laboratory.id)


@login_required
def workflow_stage_move(request, laboratory_id, stage_id, direction):
    """
    Moves a stage one position up or down in the sequence.
    """

    laboratory = _get_laboratory_for(request, laboratory_id)

    stage = WorkflowStageSelector.get_by_id(laboratory, stage_id)

    if stage is None:
        messages.error(request, "Stage not found in this laboratory.")
    elif request.method == "POST":
        try:
            WorkflowStageService.move(stage, direction)
        except ValueError as error:
            messages.error(request, str(error))

    return redirect("workflow_stage_list", laboratory_id=laboratory.id)
