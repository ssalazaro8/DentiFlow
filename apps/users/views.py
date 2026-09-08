from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LaboratoryUserForm


@login_required
def laboratory_user_create(request):
    if request.method == "POST":
        form = LaboratoryUserForm(request.POST)

        if form.is_valid():
            form.save()
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
        form = LaboratoryUserForm()

    return render(
        request,
        "users/create.html",
        {"form": form},
    )