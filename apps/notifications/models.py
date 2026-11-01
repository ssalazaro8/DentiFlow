from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    FR-12: aviso para un usuario sobre un caso o un material.

    Guarda quien lo recibe, el mensaje, si ya lo leyo y cuando se genero.
    """

    class Kind(models.TextChoices):
        CASE_STATUS = "CASE_STATUS", "Case status"
        STOCK_ALERT = "STOCK_ALERT", "Stock alert"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    message = models.CharField(max_length=255)

    # Que caso o material se vio afectado. Si luego se borran, el aviso
    # se conserva con su mensaje.
    dental_case = models.ForeignKey(
        "dental_cases.DentalCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    material = models.ForeignKey(
        "inventory.Material",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.message}"