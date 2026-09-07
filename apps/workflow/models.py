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
