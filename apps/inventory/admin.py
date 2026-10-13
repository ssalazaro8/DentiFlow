from django.contrib import admin

from .models import Material, MaterialConsumption


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "stock_quantity",
        "unit_type",
        "reorder_level",
    )

@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        "dental_case",
        "material",
        "quantity",
        "consumed_at",
        "registered_by",
    )