from django.urls import path
from . import views


urlpatterns = [
    path("", views.laboratory_list, name="laboratory_list"),
    path("search/", views.laboratory_search, name="laboratory_search"),
    path("create/", views.laboratory_create, name="laboratory_create"),
    path("<int:laboratory_id>/technicians/create/", views.technician_create, name="technician_create"),
]
