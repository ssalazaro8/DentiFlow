from .models import Workflow


class WorkflowSelector:

    @staticmethod
    def get_all():
        return Workflow.objects.all()

    @staticmethod
    def get_by_case(case_number):
        return Workflow.objects.filter(
            case_number=case_number
        )

    @staticmethod
    def get_by_id(id):
        return Workflow.objects.get(id=id)