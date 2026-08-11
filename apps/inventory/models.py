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
