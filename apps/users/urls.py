from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path(
        "create/",
        views.laboratory_user_create,
        name="create",
    ),
]