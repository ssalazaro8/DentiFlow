from django.shortcuts import redirect, render

from .services import MaterialService


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