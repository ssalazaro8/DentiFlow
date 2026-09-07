from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import WorkflowForm
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


@login_required
def workflow_create(request):

    if request.method == "POST":
        form = WorkflowForm(request.POST)

        if form.is_valid():
            WorkflowService.create(
                form.cleaned_data
            )

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


@login_required
def workflow_update_stage(request, id):

    workflow = WorkflowService.get_by_id(id)

    if request.method == "POST":

        stage = request.POST.get("stage")

        WorkflowService.update_stage(
            workflow,
            stage,
            request.user
        )

        return redirect("workflow_list")

    return render(
        request,
        "workflow/update.html",
        {
            "workflow": workflow
        }
    )


@login_required
def workflow_history(request, id):

    workflow = WorkflowService.get_by_id(id)

    history = WorkflowService.get_status_history(
        workflow
    )

    return render(
        request,
        "workflow/history.html",
        {
            "workflow": workflow,
            "history": history
        }
    )