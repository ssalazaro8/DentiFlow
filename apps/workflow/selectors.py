from .models import Workflow, WorkflowStage


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


class WorkflowStageSelector:
    """
    FR-23: consultas de la configuracion de etapas de un laboratorio.

    Toda consulta arranca del laboratorio, para que sea imposible
    devolver etapas de otro por descuido.
    """

    @staticmethod
    def get_for_laboratory(laboratory, only_active=False):
        """
        Returns the stages of a laboratory, in its configured order.
        """

        stages = WorkflowStage.objects.filter(laboratory=laboratory)

        if only_active:
            stages = stages.filter(is_active=True)

        return stages

    @staticmethod
    def get_by_id(laboratory, stage_id):
        """
        Returns one stage, only if it belongs to that laboratory.
        """

        return WorkflowStage.objects.filter(
            laboratory=laboratory,
            id=stage_id,
        ).first()

    @staticmethod
    def get_next_order(laboratory):
        """
        Returns the position a new stage should take.
        """

        ultima = (
            WorkflowStage.objects.filter(laboratory=laboratory)
            .order_by("-order")
            .first()
        )

        return (ultima.order + 1) if ultima else 1
