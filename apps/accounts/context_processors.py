from .permissions import Operation, can, get_home
from .screens import build_menu, describe_role

OPERATIONS = [
    value for name, value in vars(Operation).items() if not name.startswith("_")
]


def navigation(request):
    """
    Exposes the menu and the role of the signed in user to the templates.
    """

    user = getattr(request, "user", None)

    if user is None or not user.is_authenticated:
        return {}

    laboratory, role = get_home(user)

    return {
        "menu": build_menu(user, request.path),
        "user_role": describe_role(user),
        # Lets the templates hide the buttons of screens the role cannot open.
        "user_can": {operation: can(user, operation) for operation in OPERATIONS},
        "user_laboratory_id": laboratory.pk if laboratory else None,
    }
