from django.db import models
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