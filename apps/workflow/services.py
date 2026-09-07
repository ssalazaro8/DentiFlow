from .models import Workflow, CaseStatusHistory
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
    def create(data):
        return Workflow.objects.create(
            **data
        )

    @staticmethod
    def update_stage(workflow, stage, user):

        previous_stage = workflow.current_stage

        # Si el estado no cambió, no se crea historial
        if previous_stage == stage:
            return workflow

        workflow.current_stage = stage
        workflow.save()

        CaseStatusHistory.objects.create(
            workflow=workflow,
            previous_status=previous_stage,
            new_status=stage,
            changed_by=user
        )

        return workflow

    @staticmethod
    def get_status_history(workflow):
        return workflow.status_history.all()