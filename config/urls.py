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
]
