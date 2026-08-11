from .models import Workflow

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
    def update_stage(workflow, stage):
        workflow.current_stage = stage
        workflow.save()

        return workflow