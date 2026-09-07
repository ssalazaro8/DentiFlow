from django.conf import settings
from django.db import models


class Workflow(models.Model):

    STAGE_CHOICES = [
        ("RECEIVED", "Received"),
        ("DESIGN", "3D Design"),
        ("PRINTING", "Printing / Milling"),
        ("QC", "Quality Control"),
        ("SHIPPED", "Shipped"),
    ]

    case_number = models.CharField(
        max_length=20
    )

    current_stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default="RECEIVED"
    )

    comments = models.TextField(
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"

    def __str__(self):
        return f"{self.case_number} - {self.current_stage}"


class CaseStatusHistory(models.Model):

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="status_history"
    )

    previous_status = models.CharField(
        max_length=20
    )

    new_status = models.CharField(
        max_length=20
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="case_status_changes"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Case Status History"
        verbose_name_plural = "Case Status Histories"

    def __str__(self):
        return (
            f"{self.workflow.case_number}: "
            f"{self.previous_status} → {self.new_status}"
        )