from django.contrib import admin

from .models import DentalCase, TechnicianAssignment


@admin.register(DentalCase)
class DentalCaseAdmin(admin.ModelAdmin):

    list_display = (
        "case_number",
        "clinic_name",
        "requested_by",
        "service_type",
        "status",
        "acceptance_status",
        "laboratory",
        "due_date",
        "created_at",
    )

    list_filter = (
        "status",
        "acceptance_status",
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


@admin.register(TechnicianAssignment)
class TechnicianAssignmentAdmin(admin.ModelAdmin):
    list_display = ("dental_case", "technician", "assigned_at")
    search_fields = ("dental_case__case_number", "technician__username")
