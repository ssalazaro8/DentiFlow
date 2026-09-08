from django.urls import path
from .views import download_case_file_view

app_name = "dental_cases"

urlpatterns = [
    path("files/<int:file_id>/download/", download_case_file_view, name="download_file"),
]