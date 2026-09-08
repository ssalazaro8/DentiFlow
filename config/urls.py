"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Clinics
    path("clinics/", include("apps.clinics.urls")),

    # Accounts
    path("accounts/", include("django.contrib.auth.urls")),

    # Laboratories
    path("laboratories/", include("apps.laboratories.urls")),

    # Dental cases
    path("cases/", include("apps.dental_cases.urls")),

    # Workflow
    path("workflow/", include("apps.workflow.urls")),

    # Inventory
    path("inventory/", include("apps.inventory.urls")),

    # Operational reports
    path("reports/", include("apps.reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )