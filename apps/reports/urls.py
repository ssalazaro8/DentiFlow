from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.OperationalReportsView.as_view(),
        name="operational_reports",
    ),

    path(
        "download/<str:report_type>/",
        views.download_report_view,
        name="download_report",
    ),
]
