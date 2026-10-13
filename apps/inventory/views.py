from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.dental_cases.models import DentalCase

from .forms import MaterialConsumptionForm
from .permissions import can_register_consumption
from .services import MaterialConsumptionService, MaterialService

def material_list(request):

    materials = MaterialService.get_all()

    return render(
        request,
        "inventory/list.html",
        {
            "materials": materials
        }
    )


def material_update_stock(request, id):

    material = MaterialService.get_by_id(id)

    if request.method == "POST":

        stock_quantity = request.POST.get("stock_quantity")

        MaterialService.update_stock(
            material,
            stock_quantity
        )

        return redirect("material_list")

    return render(
        request,
        "inventory/update.html",
        {
            "material": material
        }
    )

@login_required
@require_POST
def register_material_consumption(request, case_id):
    """FR-13: records the materials a case consumed and updates the stock."""

    dental_case = get_object_or_404(DentalCase, pk=case_id)

    if not can_register_consumption(request.user, dental_case):
        raise PermissionDenied(
            "You are not authorized to record materials for this case."
        )

    form = MaterialConsumptionForm(request.POST)

    if form.is_valid():
        try:
            MaterialConsumptionService.register(
                dental_case=dental_case,
                material=form.cleaned_data["material"],
                quantity=form.cleaned_data["quantity"],
                user=request.user,
            )
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, "Material consumption recorded.")
    else:
        messages.error(request, "Select a material and enter a quantity greater than zero.")

    return redirect("dental_case_detail", case_id=case_id)