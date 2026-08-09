from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.material_list,
        name="material_list"
    ),

    path(
        "<int:id>/update/",
        views.material_update_stock,
        name="material_update_stock"
    ),
]