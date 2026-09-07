from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.workflow_list,
        name="workflow_list"
    ),

    path(
        "create/",
        views.workflow_create,
        name="workflow_create"
    ),

    path(
        "<int:id>/update/",
        views.workflow_update_stage,
        name="workflow_update_stage"
    ),

    path(
        "<int:id>/history/",
        views.workflow_history,
        name="workflow_history"
    ),
]

