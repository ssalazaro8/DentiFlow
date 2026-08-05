from django.shortcuts import render

from .forms import WorkflowForm

from .services import WorkflowService


def workflow_list(request):

    workflows = WorkflowService.get_all()

    return render(
        request,
        "workflow/list.html",
        {
            "workflows": workflows
        }
    )


def workflow_create(request):

    form = WorkflowForm()

    return render(
        request,
        "workflow/create.html",
        {
            "form": form
        }
    )
