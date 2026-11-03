from django.contrib import admin

from .models import LaboratoryUser


@admin.register(LaboratoryUser)
class LaboratoryUserAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "laboratory",
        "role",
        "status",
        "user",
    )
    list_filter = ("role", "status", "laboratory")
    search_fields = ("first_name", "last_name", "email", "user__username")
