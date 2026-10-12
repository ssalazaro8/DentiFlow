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

from django.contrib.auth.decorators import login_required
from apps.dental_cases.services import DentalCaseService

@login_required
def clinic_detail(request, clinic_id):
    """Clinic detail page showing their cases."""
    clinic = get_object_or_404(Clinic, pk=clinic_id)
    cases = DentalCaseService.get_all().filter(clinic=clinic).order_by('-created_at')
    return render(request, "clinics/detail.html", {"clinic": clinic, "cases": cases})
