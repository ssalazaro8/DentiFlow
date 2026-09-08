from django.db import models
from django.conf import settings
from apps.dental_cases.models import DentalCase
from django.db import models


class Workflow(models.Model):

    STAGE_CHOICES = [
        ("RECEIVED", "Received"),
        ("DESIGN", "3D Design"),
        ("PRINTING", "Printing / Milling"),
        ("QC", "Quality Control"),
        ("SHIPPED", "Shipped"),
    ]

    dental_case = models.OneToOneField(
        DentalCase,
        on_delete=models.CASCADE,
        related_name="workflow",
        null=True,
        blank=True,
    )

    current_stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default="RECEIVED"
    )

    comments = models.TextField(
        blank=True
    )

    progress_percentage = models.PositiveSmallIntegerField(default=0)

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"

    def __str__(self):
        return f"{self.dental_case} - {self.current_stage}"


class WorkflowUpdate(models.Model):
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="updates",
    )
    # Etapa desde la que se movio el caso. Queda vacia en el primer
    # registro, cuando el workflow recien se crea y no hay anterior.
    previous_stage = models.CharField(
        max_length=20,
        choices=Workflow.STAGE_CHOICES,
        blank=True,
        verbose_name="Previous stage",
    )
    stage = models.CharField(max_length=20, choices=Workflow.STAGE_CHOICES)
    progress_percentage = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="workflow_updates",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Workflow Update"
        verbose_name_plural = "Workflow Updates"

    def __str__(self):
        origen = self.get_previous_stage_display() or "Start"
        return f"{origen} -> {self.get_stage_display()}"


class WorkflowStage(models.Model):
    """
    FR-23: una etapa de produccion configurable por laboratorio.

    Cada laboratorio arma su propia secuencia. La configuracion de uno
    nunca alcanza a la de otro, porque toda consulta parte del FK.
    """

    laboratory = models.ForeignKey(
        "laboratories.Laboratory",
        on_delete=models.CASCADE,
        related_name="workflow_stages",
        verbose_name="Laboratory",
    )

    name = models.CharField(
        max_length=60,
        verbose_name="Stage name",
    )

    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Order",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Se muestran en el orden que definio el laboratorio; el nombre
        # solo desempata cuando dos comparten posicion.
        ordering = ["order", "name"]
        verbose_name = "Workflow Stage"
        verbose_name_plural = "Workflow Stages"
        constraints = [
            models.UniqueConstraint(
                fields=["laboratory", "name"],
                name="unique_stage_name_per_laboratory",
            ),
        ]

    def __str__(self):
        return f"{self.laboratory.name} - {self.order}. {self.name}"
