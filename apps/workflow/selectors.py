from datetime import timedelta

from .models import Workflow, WorkflowStage, WorkflowUpdate
from django.db.models import Prefetch
from django.utils import timezone


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


class WorkflowUpdateSelector:
    """
    FR-11: Consultas para la línea de tiempo de cambios de etapas.
    """

    @staticmethod
    def get_timeline_for_workflow(workflow):
        """
        Obtiene todos los cambios de etapas de un workflow en orden cronológico.
        Incluye información del usuario responsable y cálculo de tiempo transcurrido.
        """
        updates = WorkflowUpdate.objects.filter(
            workflow=workflow
        ).select_related('updated_by').order_by('created_at')

        return updates

    @staticmethod
    def get_average_stage_durations(service_type="", date_from=None, date_to=None):
        """
        FR-37: promedio de permanencia por etapa. Cada permanencia va desde un
        cambio de etapa hasta el siguiente del mismo caso y se cuenta si su
        entrada cae dentro del rango de fechas.
        """
        updates = list(
            WorkflowUpdate.objects.select_related("workflow__dental_case")
            .order_by("workflow_id", "created_at")
        )
        if service_type:
            updates = [u for u in updates if u.workflow.dental_case.service_type == service_type]

        durations = {}
        for current, following in zip(updates, updates[1:]):
            if current.workflow_id != following.workflow_id:
                continue
            day = timezone.localdate(current.created_at)
            if (date_from and day < date_from) or (date_to and day > date_to):
                continue
            durations.setdefault(current.stage, []).append(following.created_at - current.created_at)

        return [
            {
                "stage": code,
                "label": label,
                "average": sum(durations[code], timedelta()) / len(durations[code]),
                "cases": len(durations[code]),
            }
            for code, label in Workflow.STAGE_CHOICES
            if code in durations
        ]

    @staticmethod
    def get_timeline_with_elapsed_time(workflow):
        """
        Obtiene el timeline con el tiempo transcurrido entre cada evento.
        """
        updates = WorkflowUpdateSelector.get_timeline_for_workflow(workflow)
        timeline = []

        for i, update in enumerate(updates):
            elapsed_time = None
            if i > 0:
                prev_update = updates[i - 1]
                elapsed_time = update.created_at - prev_update.created_at

            timeline.append({
                'update': update,
                'elapsed_time': elapsed_time,
            })

        return timeline
