from django.contrib import admin
from .models import Clinic


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "phone", "is_active")
    search_fields = ("name", "nit", "city")
    # FR-16: the accounts of the clinic's people are linked here.
    filter_horizontal = ("users",)
