from django.shortcuts import render, redirect
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
    if request.method == "POST":
        form = ClinicForm(request.POST)
        if form.is_valid():
            ClinicService.create(form.cleaned_data)
            return redirect("clinic_list")
    else:
        form = ClinicForm()
    return render(
        request,
        "clinics/create.html",
        {
            "form": form
        }
    )