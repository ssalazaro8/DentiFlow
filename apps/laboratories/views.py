from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .forms import LaboratoryForm, TechnicianCreateForm
from .models import Laboratory
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


def technician_create(request, laboratory_id):
    laboratory = get_object_or_404(
        Laboratory,
        pk=laboratory_id,
    )

    form = TechnicianCreateForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        User = get_user_model()

        technician = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
        )

        # IMPORTANT:
        # Associate the new technician ONLY with this laboratory.
        laboratory.technicians.add(technician)

        return redirect(
            "laboratory_list"
        )

    return render(
        request,
        "laboratories/technician_create.html",
        {
            "laboratory": laboratory,
            "form": form,
        },
    )