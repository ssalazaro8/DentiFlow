from django.core.exceptions import PermissionDenied

from apps.laboratories.models import Laboratory

from .permissions import INACTIVE_ACCOUNT_MESSAGE, is_blocked, require
from .screens import SCREEN_OPERATIONS

# An inactive laboratory user can still get in and out, nothing else.
OPEN_TO_INACTIVE_ACCOUNTS = {"login", "logout"}


class RoleAccessMiddleware:
    """
    Verifies the role of the user before a protected screen runs (FR-16).

    Signing in is enforced before this by Django's own
    LoginRequiredMiddleware, so here the user is already known.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):

        user = request.user

        if not user.is_authenticated:
            return None

        match = request.resolver_match

        # The administration site applies its own permissions.
        if "admin" in match.namespaces:
            return None

        if is_blocked(user) and match.view_name not in OPEN_TO_INACTIVE_ACCOUNTS:
            raise PermissionDenied(INACTIVE_ACCOUNT_MESSAGE)

        operation = SCREEN_OPERATIONS.get(match.view_name)

        if operation is None:
            return None

        laboratory = None

        if "laboratory_id" in view_kwargs:

            laboratory = Laboratory.objects.filter(
                pk=view_kwargs["laboratory_id"]
            ).first()

            # An unknown laboratory is the view's business: it answers 404.
            if laboratory is None:
                return None

        require(user, operation, laboratory)

        return None
