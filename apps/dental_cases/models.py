from django.db import models


class DentalCase(models.Model):

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
        unique=True
    )

    clinic_name = models.CharField(
        max_length=150
    )

    requested_by = models.CharField(
        max_length=150
    )

    patient_reference = models.CharField(
        max_length=100,
        blank=True
    )

    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES
    )

    description = models.TextField()

    observations = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Dental Case"
        verbose_name_plural = "Dental Cases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case_number}"