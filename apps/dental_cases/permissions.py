from django.core.exceptions import PermissionDenied

# Shown to the user when they are not related to the case. It stays
# deliberately vague: confirming that a case exists is already more
# than an unrelated user should learn.
ACCESS_DENIED_MESSAGE = (
    "You are not authorized to access the files of this dental case."
)


def can_access_case(user, dental_case):
    """
    Returns whether the user may see a dental case and its files.

    Access is granted to superusers, to the account that submitted the
    case, and to the users authorised in the destination laboratory.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if dental_case.created_by_id == user.id:
        return True

    return bool(
        dental_case.laboratory
        and dental_case.laboratory.authorized_users.filter(
            pk=user.pk
        ).exists()
    )


def require_case_access(user, dental_case):
    """
    Raises PermissionDenied when the user may not access the case.
    """

    if not can_access_case(user, dental_case):
        raise PermissionDenied(ACCESS_DENIED_MESSAGE)
