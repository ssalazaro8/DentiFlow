from django.contrib import admin

from .models import DentalCase


@admin.register(DentalCase)
class DentalCaseAdmin(admin.ModelAdmin):

    list_display = (
        "case_number",
        "clinic_name",
        "requested_by",
        "service_type",
        "status",
        "due_date",
        "created_at",
    )

    list_filter = (
        "status",
        "service_type",
        "due_date",
    )

    search_fields = (
        "case_number",
        "clinic_name",
        "requested_by",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 20