from django.conf import settings
from django.db import models


class Clinic(models.Model):

    name = models.CharField(
        max_length=150
    )

    nit = models.CharField(
        max_length=20,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=20
    )

    address = models.CharField(
        max_length=250
    )

    city = models.CharField(
        max_length=80
    )

    contact_person = models.CharField(
        max_length=150
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # FR-16: the accounts of the people who work at the clinic. They
    # send the clinic's cases and follow only those.
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="clinics",
        verbose_name="Users",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Clinic"
        verbose_name_plural = "Clinics"

    def __str__(self):
        return self.name
