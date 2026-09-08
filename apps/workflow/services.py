from django.db import transaction

from apps.dental_cases.models import DentalCase
from .models import Workflow, WorkflowStage, WorkflowUpdate

from .selectors import WorkflowSelector, WorkflowStageSelector


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


class WorkflowStageService:
    """
    FR-23: alta, edicion, activacion y reordenamiento de etapas.

    Cada metodo recibe el laboratorio y trabaja siempre dentro de el,
    de modo que una operacion no pueda tocar la configuracion de otro.
    """

    @staticmethod
    def get_stages(laboratory, only_active=False):
        return WorkflowStageSelector.get_for_laboratory(
            laboratory, only_active=only_active
        )

    @staticmethod
    @transaction.atomic
    def create(laboratory, name, is_active=True):
        """
        Creates a stage at the end of the laboratory's sequence.
        """

        name = name.strip()

        if not name:
            raise ValueError("The stage name cannot be empty.")

        if WorkflowStage.objects.filter(
            laboratory=laboratory, name__iexact=name
        ).exists():
            raise ValueError(
                f'The stage "{name}" already exists in this laboratory.'
            )

        return WorkflowStage.objects.create(
            laboratory=laboratory,
            name=name,
            order=WorkflowStageSelector.get_next_order(laboratory),
            is_active=is_active,
        )

    @staticmethod
    @transaction.atomic
    def update(stage, name=None, is_active=None):
        """
        Renames a stage or changes whether it is active.
        """

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError("The stage name cannot be empty.")

            duplicada = (
                WorkflowStage.objects.filter(
                    laboratory=stage.laboratory, name__iexact=name
                )
                .exclude(pk=stage.pk)
                .exists()
            )

            if duplicada:
                raise ValueError(
                    f'The stage "{name}" already exists in this laboratory.'
                )

            stage.name = name

        if is_active is not None:
            stage.is_active = is_active

        stage.save()

        return stage

    @staticmethod
    def toggle_active(stage):
        """
        Activates a stage if it was inactive, and the other way round.
        """

        return WorkflowStageService.update(
            stage, is_active=not stage.is_active
        )

    @staticmethod
    @transaction.atomic
    def move(stage, direction):
        """
        Moves a stage one position up or down.

        The swap only looks at the stages of the same laboratory, so
        reordering never reaches another laboratory's sequence.
        """

        if direction not in ("up", "down"):
            raise ValueError("Direction must be 'up' or 'down'.")

        hermanas = WorkflowStage.objects.filter(
            laboratory=stage.laboratory
        )

        if direction == "up":
            vecina = (
                hermanas.filter(order__lt=stage.order)
                .order_by("-order")
                .first()
            )
        else:
            vecina = (
                hermanas.filter(order__gt=stage.order)
                .order_by("order")
                .first()
            )

        # Ya esta en un extremo: no es un error, simplemente no se mueve.
        if vecina is None:
            return stage

        stage.order, vecina.order = vecina.order, stage.order

        stage.save(update_fields=["order", "updated_at"])
        vecina.save(update_fields=["order", "updated_at"])

        return stage

    @staticmethod
    @transaction.atomic
    def delete(stage):
        stage.delete()
