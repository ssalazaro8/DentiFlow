<<<<<<< HEAD
"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clinics/', include('apps.clinics.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('laboratories/', include('apps.laboratories.urls')),
=======
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "cases/",
        include(
            "apps.dental_cases.urls"
        ),
    ),
>>>>>>> origin/dev
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )