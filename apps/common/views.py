from django.shortcuts import redirect


def home(request):
    """Punto de entrada: cada usuario cae en el lugar que le corresponde."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")