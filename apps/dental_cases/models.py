from django.db import models


class DentalCase(models.Model):

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        IN_REVIEW = "IN_REVIEW", "In Review"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    SERVICE_TYPES = [
        ("CROWN", "Dental Crown"),
        ("BRIDGE", "Dental Bridge"),
        ("IMPLANT", "Dental Implant"),
        ("VENEER", "Dental Veneer"),
        ("ORTHODONTICS", "Orthodontics"),
        ("OTHER", "Other"),
    ]

    case_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Case Number",
    )

    clinic_name = models.CharField(
        max_length=150,
        verbose_name="Clinic",
    )

    requested_by = models.CharField(
        max_length=150,
        verbose_name="Requested By",
    )

    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        verbose_name="Service Type",
    )

    description = models.TextField(
        verbose_name="Description",
    )

    observations = models.TextField(
        blank=True,
        verbose_name="Observations",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        verbose_name="Status",
    )

    due_date = models.DateField(
        verbose_name="Due Date",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        verbose_name = "Dental Case"
        verbose_name_plural = "Dental Cases"
        ordering = ["-created_at"]

    def __str__(self):
        return self.case_number