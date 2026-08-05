from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.clinic_list,
        name="clinic_list"
    ),

    path(
        "create/",
        views.clinic_create,
        name="clinic_create"
    ),

]