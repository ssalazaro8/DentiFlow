from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from .forms import LaboratoryForm
from .services import LaboratoryService


def laboratory_list(request):
    """Muestra la lista de todos los laboratorios."""
    laboratories = LaboratoryService.get_all()
    return render(
        request,
        "laboratories/list.html",
        {"laboratories": laboratories}
    )


def laboratory_search(request):
    """Filtra laboratorios según lo que el usuario busque en la URL."""
    city = request.GET.get("city")
    service = request.GET.get("service")
    min_rating = request.GET.get("min_rating")
    laboratories = LaboratoryService.search(city=city, service=service, min_rating=min_rating)

    return render(
        request,
        "laboratories/search.html",
        {"laboratories": laboratories}
    )


def laboratory_create(request):
    """Muestra el formulario y procesa la creación de un nuevo laboratorio."""
    if request.method == "POST":
        # Si el usuario le dio a "Guardar" / "Enviar"
        form = LaboratoryForm(request.POST)
        if form.is_valid():
            # Si los datos son correctos, los guarda usando el servicio
            LaboratoryService.create(form.cleaned_data)
            return redirect("laboratory_list")  # Redirige a la lista
    else:
        # Si el usuario solo abrió la página para ver el formulario limpio
        form = LaboratoryForm()

    return render(
        request,
        "laboratories/create.html",
        {"form": form}
    )
