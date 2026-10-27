from django.shortcuts import redirect

from apps.accounts.screens import home_url


def home(request):
    """Punto de entrada: cada usuario cae en el lugar que le corresponde."""
    if request.user.is_authenticated:
        # FR-16: cada rol empieza en su propia pantalla.
        return redirect(home_url(request.user))
    return redirect("login")
