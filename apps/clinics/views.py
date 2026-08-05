from django.shortcuts import render
from .forms import ClinicForm
from .services import ClinicService


def clinic_list(request):

    clinics = ClinicService.get_all()

    return render(
        request,
        "clinics/list.html",
        {
            "clinics": clinics
        }
    )


def clinic_create(request):

    form = ClinicForm()

    return render(
        request,
        "clinics/create.html",
        {
            "form": form
        }
    )