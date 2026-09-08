from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.dental_cases.models import DentalCase
from apps.dental_cases.services import DentalCaseService
from apps.dental_cases.views import _can_view_case
from .forms import WorkflowForm, WorkflowUpdateForm
from .models import Workflow, WorkflowUpdate
from .services import WorkflowService


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
