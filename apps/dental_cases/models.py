import os
from django.db import models
from django.conf import settings
from apps.laboratories.models import Laboratory
from apps.clinics.models import Clinic


class DentalCase(models.Model):

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        IN_REVIEW = "IN_REVIEW", "In Review"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        REJECTED = "REJECTED", "Rejected"

    class AcceptanceStatus(models.TextChoices):
        PENDING = "PENDING", "Pending laboratory decision"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

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

    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.PROTECT,
        related_name="dental_cases",
        null=True,
        blank=True,
    )

    laboratory = models.ForeignKey(
        Laboratory,
        on_delete=models.PROTECT,
        related_name="dental_cases",
        null=True,
        blank=True,
        verbose_name="Destination laboratory",
    )

    # The clinic/dentist account that submitted this private case.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_dental_cases",
        null=True,
        blank=True,
    )

    acceptance_status = models.CharField(
        max_length=12,
        choices=AcceptanceStatus.choices,
        default=AcceptanceStatus.PENDING,
        verbose_name="Laboratory decision",
    )

    rejection_reason = models.TextField(blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

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

    def __str__(self) -> str:
        return str(self.case_number)


class TechnicianAssignment(models.Model):
    """The current technician assigned to an accepted dental case."""

    dental_case = models.OneToOneField(
        DentalCase,
        on_delete=models.CASCADE,
        related_name="technician_assignment",
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="technician_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dental_case.case_number} - {self.technician}"


class DentalCaseFile(models.Model):
    case = models.ForeignKey(
        DentalCase,
        on_delete=models.CASCADE,
        related_name="case_files",
        verbose_name="Dental Case",
    )
    file = models.FileField(
        upload_to="case_files/",
        verbose_name="File",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Uploaded At",
    )

    class Meta:
        verbose_name = "Dental Case File"
        verbose_name_plural = "Dental Case Files"

    def __str__(self) -> str:
        return f"{self.case.case_number} - {self.filename}"  # pylint: disable=no-member

    @property
    def filename(self) -> str:
        if self.file and hasattr(self.file, "name"):
            return os.path.basename(self.file.name)
        return ""
