from django.shortcuts import get_object_or_404, render, redirect
from .forms import ClinicForm
from .models import Clinic
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
from apps.accounts.permissions import require_clinic_access
from apps.dental_cases.services import DentalCaseService

@login_required
def clinic_detail(request, clinic_id):
    """Clinic detail page showing their cases."""
    clinic = get_object_or_404(Clinic, pk=clinic_id)
    # FR-16: only the cases the user may see, never the whole clinic.
    require_clinic_access(request.user, clinic)
    cases = (
        DentalCaseService.get_visible_cases(request.user)
        .filter(clinic=clinic)
        .order_by('-created_at')
    )
    return render(request, "clinics/detail.html", {"clinic": clinic, "cases": cases})
