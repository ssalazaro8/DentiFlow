from django.conf import settings
from django.db import models


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
