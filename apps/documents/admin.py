from django.contrib import admin

from .models import CaseFile


@admin.register(CaseFile)
class CaseFileAdmin(
    admin.ModelAdmin
):

    list_display = (
        "original_name",
        "dental_case",
        "category",
        "uploaded_at",
    )

    list_filter = (
        "category",
        "uploaded_at",
    )

    search_fields = (
        "original_name",
        "dental_case__case_number",
    )

    readonly_fields = (
        "original_name",
        "uploaded_at",
    )