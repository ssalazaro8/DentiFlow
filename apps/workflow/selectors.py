from .models import Workflow


class WorkflowSelector:

    @staticmethod
    def get_all():
        return Workflow.objects.select_related("dental_case").all()

    @staticmethod
    def get_by_case(case_number):
        return Workflow.objects.select_related("dental_case").filter(dental_case__case_number=case_number)

    @staticmethod
    def get_by_id(id):
        return Workflow.objects.select_related("dental_case__laboratory").get(id=id)
