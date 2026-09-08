from django.db import transaction

from apps.dental_cases.models import DentalCase
from .models import Workflow, WorkflowUpdate

from .selectors import WorkflowSelector


class WorkflowService:

    @staticmethod
    def get_all():
        return WorkflowSelector.get_all()

    @staticmethod
    def get_by_case(case_number):
        return WorkflowSelector.get_by_case(
            case_number
        )

    @staticmethod
    def get_by_id(id):
        return WorkflowSelector.get_by_id(id)

    @staticmethod
    @transaction.atomic
    def create(data):
        dental_case = data["dental_case"]
        if dental_case.acceptance_status != DentalCase.AcceptanceStatus.ACCEPTED:
            raise ValueError("A workflow can only be started for an accepted case.")
        workflow = Workflow.objects.create(**data)
        WorkflowUpdate.objects.create(
            workflow=workflow,
            previous_stage="",
            stage=workflow.current_stage,
            progress_percentage=workflow.progress_percentage,
            comment=workflow.comments,
        )
        return workflow

    @staticmethod
    @transaction.atomic
    def update_stage(workflow, stage, progress_percentage, comment, user=None):
        if not workflow or not workflow.dental_case:
            raise ValueError("Workflow not found.")
        if workflow.dental_case.acceptance_status != DentalCase.AcceptanceStatus.ACCEPTED:
            raise ValueError("Rejected cases cannot proceed through production.")

        # Se lee antes de pisarlo: es el "de donde venia" del historial.
        previous_stage = workflow.current_stage

        workflow.current_stage = stage
        workflow.progress_percentage = progress_percentage
        workflow.comments = comment
        workflow.save()
        WorkflowUpdate.objects.create(
            workflow=workflow,
            previous_stage=previous_stage,
            stage=stage,
            progress_percentage=progress_percentage,
            comment=comment,
            updated_by=user if getattr(user, "is_authenticated", False) else None,
        )

        return workflow

    @staticmethod
    def get_status_history(workflow):
        """
        Returns the full ordered history of a workflow.
        """

        return workflow.updates.select_related("updated_by").all()
