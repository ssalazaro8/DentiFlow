from django.urls import include, path

from . import views


urlpatterns = [

    path(
        "",
        views.dental_case_list,
        name="dental_case_list",
    ),

    path(
        "create/",
        views.dental_case_create,
        name="dental_case_create",
    ),

    path(
        "<int:case_id>/",
        views.dental_case_detail,
        name="dental_case_detail",
    ),

    path(
        "<int:case_id>/edit/",
        views.dental_case_edit,
        name="dental_case_edit",
    ),

    path(
        "<int:case_id>/delete/",
        views.dental_case_delete,
        name="dental_case_delete",
    ),

    path(
        "<int:case_id>/files/",
        include(
            "apps.documents.urls"
        ),
    ),

    # FR-24: descarga de archivos adjuntos
    path(
        "files/<int:file_id>/download/",
        views.download_case_file_view,
        name="download_file",
    ),
]
