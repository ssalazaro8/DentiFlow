from django.contrib import admin

from .models import Material, MaterialConsumption, StockAlert
from .services import StockAlertService


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "stock_quantity",
        "unit_type",
        "reorder_level",
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # FR-28: crear o editar un material desde el admin tambien
        # revisa el stock minimo.
        StockAlertService.sync(obj)


@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        "dental_case",
        "material",
        "quantity",
        "consumed_at",
        "registered_by",
    )


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = (
        "material",
        "status",
        "stock_when_opened",
        "reorder_level_when_opened",
        "opened_at",
        "closed_at",
    )
    list_filter = ("status",)