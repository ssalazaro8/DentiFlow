from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

from .forms import DentalCaseForm

from .services import DentalCaseService


def dental_case_list(request):

    dental_cases = DentalCaseService.get_all()

    return render(
        request,
        "dental_cases/list.html",
        {
            "dental_cases": dental_cases
        }
    )


def dental_case_create(request):

    form = DentalCaseForm()

    return render(
        request,
        "dental_cases/create.html",
        {
            "form": form
        }
    )