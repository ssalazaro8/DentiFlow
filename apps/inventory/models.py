from django.conf import settings
from django.db import models
from django.db.models import Q


class Material(models.Model):
    UNIT_CHOICES = [
        ("UNIT", "Units"),
        ("GRAM", "Grams"),
        ("MILLILITER", "Milliliters"),
    ]

    name = models.CharField(max_length=100)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_type = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
    )
    reorder_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Material"
        verbose_name_plural = "Materials"

    def __str__(self):
        return self.name

class MaterialConsumption(models.Model):
    
    
    # FR-13: material consumido por un caso dental durante su produccion.
    

    dental_case = models.ForeignKey(
        "dental_cases.DentalCase",
        on_delete=models.CASCADE,
        related_name="material_consumptions",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="consumptions",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    consumed_at = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="material_consumptions",
    )

    class Meta:
        ordering = ["-consumed_at", "-id"]
        verbose_name = "Material Consumption"
        verbose_name_plural = "Material Consumptions"

    def __str__(self):
        return f"{self.dental_case} - {self.material} x {self.quantity}"

class StockAlert(models.Model):
    """
    FR-28: alerta de stock minimo de un material.

    Mientras el material siga en o bajo su nivel minimo hay una sola alerta
    abierta. Cuando el stock se recupera la alerta se cierra y queda como
    historial.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="stock_alerts",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    stock_when_opened = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level_when_opened = models.DecimalField(max_digits=10, decimal_places=2)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-opened_at", "-id"]
        verbose_name = "Stock Alert"
        verbose_name_plural = "Stock Alerts"
        constraints = [
            # La base de datos misma impide dos alertas abiertas del
            # mismo material.
            models.UniqueConstraint(
                fields=["material"],
                condition=Q(status="OPEN"),
                name="unique_open_stock_alert_per_material",
            )
        ]

    def __str__(self):
        return f"{self.material} - {self.get_status_display()}"
