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
    path("laboratories/<int:laboratory_id>/inbox/", views.laboratory_case_inbox, name="laboratory_case_inbox"),
    path("clinics/<int:clinic_id>/inbox/", views.clinic_case_inbox, name="clinic_case_inbox"),
    path("<int:case_id>/accept/", views.dental_case_accept, name="dental_case_accept"),
    path("<int:case_id>/reject/", views.dental_case_reject, name="dental_case_reject"),
    path("<int:case_id>/technician/", views.technician_assignment, name="technician_assignment"),
    path("<int:case_id>/technician/remove/", views.technician_assignment_remove, name="technician_assignment_remove"),

    path(
        "<int:case_id>/files/",
        include(
            "apps.documents.urls"
        ),
    ),
]
