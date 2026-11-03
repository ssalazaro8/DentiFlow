from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.permissions import get_home

from .forms import LaboratoryUserForm
from .services import LaboratoryUserService


@login_required
def laboratory_user_create(request):

    # Superusers choose the laboratory; an administrator registers
    # people in their own.
    laboratory = None

    if not request.user.is_superuser:
        laboratory, _ = get_home(request.user)

    if request.method == "POST":
        form = LaboratoryUserForm(request.POST, laboratory=laboratory)

        if form.is_valid():
            LaboratoryUserService.register(
                form.cleaned_data,
                laboratory or form.cleaned_data["laboratory"],
            )
            messages.success(
                request,
                "Laboratory user registered successfully.",
            )
            return redirect("users:create")

        messages.error(
            request,
            "Please correct the errors in the form.",
        )

    else:
        form = LaboratoryUserForm(laboratory=laboratory)

    return render(
        request,
        "users/create.html",
        {"form": form},
    )