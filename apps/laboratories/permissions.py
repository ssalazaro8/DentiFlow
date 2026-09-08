from django.core.exceptions import PermissionDenied

ACCESS_DENIED_MESSAGE = (
    "You are not authorized to manage the configuration of this laboratory."
)


def can_manage_laboratory(user, laboratory):
    """
    Returns whether the user may read and change a laboratory's setup.

    Only superusers and the users authorised in that laboratory can:
    a laboratory must never reach another one's configuration.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return laboratory.authorized_users.filter(pk=user.pk).exists()


def require_laboratory_access(user, laboratory):
    """
    Raises PermissionDenied when the user may not manage the laboratory.
    """

    if not can_manage_laboratory(user, laboratory):
        raise PermissionDenied(ACCESS_DENIED_MESSAGE)
