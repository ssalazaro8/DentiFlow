"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    path("workflow/", include("apps.workflow.urls")),

    path("inventory/", include("apps.inventory.urls")),

    path("users/", include("apps.users.urls")),

    path(
        "accounts/",
        include("django.contrib.auth.urls")
    ),
]