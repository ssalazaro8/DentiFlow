from django.core.validators import RegexValidator
from django.db import models


class LaboratoryUser(models.Model):

    ROLE_CHOICES = [
        ("ADMIN", "Administrator"),
        ("TECHNICIAN", "Technician"),
        ("RECEPTIONIST", "Receptionist"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    first_name = models.CharField(
        max_length=100,
        verbose_name="First name",
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name="Last name",
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9\s\-()]{7,20}$",
                message="Enter a valid phone number.",
            )
        ],
        verbose_name="Phone",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="TECHNICIAN",
        verbose_name="Role",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        verbose_name="Status",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Laboratory User"
        verbose_name_plural = "Laboratory Users"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"