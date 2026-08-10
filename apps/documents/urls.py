from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.case_file_list,
        name="case_file_list",
    ),

    path(
        "upload/",
        views.case_file_upload,
        name="case_file_upload",
    ),

    path(
        "<int:file_id>/delete/",
        views.case_file_delete,
        name="case_file_delete",
    ),

    path(
        "<int:file_id>/download/",
        views.case_file_download,
        name="case_file_download",
    ),
]