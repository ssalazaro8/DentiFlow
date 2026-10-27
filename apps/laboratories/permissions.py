from django.core.exceptions import PermissionDenied

from apps.accounts.permissions import Operation, can_in

ACCESS_DENIED_MESSAGE = (
    "You are not authorized to manage the configuration of this laboratory."
)


def can_manage_laboratory(user, laboratory):
    """
    Returns whether the user may read and change a laboratory's setup.

    Only superusers and the administrators of that laboratory can:
    a laboratory must never reach another one's configuration.
    """

    return can_in(
        user,
        Operation.CONFIGURE_LABORATORY,
        laboratory,
    )


def require_laboratory_access(user, laboratory):
    """
    Raises PermissionDenied when the user may not manage the laboratory.
    """

    if not can_manage_laboratory(user, laboratory):
        raise PermissionDenied(ACCESS_DENIED_MESSAGE)
