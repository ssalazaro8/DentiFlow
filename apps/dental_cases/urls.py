from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.dental_case_list,
        name="dental_case_list"
    ),

    path(
        "create/",
        views.dental_case_create,
        name="dental_case_create"
    ),

]