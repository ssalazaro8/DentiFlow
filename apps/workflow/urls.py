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
    path("<int:id>/history/", views.workflow_history, name="workflow_history"),
    path("case/<int:case_id>/", views.case_tracking, name="case_tracking"),
    path("case/<int:case_id>/start/", views.start_production, name="start_production"),

    # FR-23: configuracion de etapas por laboratorio
    path(
        "laboratories/<int:laboratory_id>/stages/",
        views.workflow_stage_list,
        name="workflow_stage_list",
    ),
    path(
        "laboratories/<int:laboratory_id>/stages/create/",
        views.workflow_stage_create,
        name="workflow_stage_create",
    ),
    path(
        "laboratories/<int:laboratory_id>/stages/<int:stage_id>/edit/",
        views.workflow_stage_edit,
        name="workflow_stage_edit",
    ),
    path(
        "laboratories/<int:laboratory_id>/stages/<int:stage_id>/toggle/",
        views.workflow_stage_toggle,
        name="workflow_stage_toggle",
    ),
    path(
        "laboratories/<int:laboratory_id>/stages/<int:stage_id>/move/<str:direction>/",
        views.workflow_stage_move,
        name="workflow_stage_move",
    ),
]
