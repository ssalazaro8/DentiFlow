from django.core.exceptions import PermissionDenied
from django.db.models import Q

from apps.accounts.permissions import (
    Operation,
    can_in,
    get_laboratories,
    is_blocked,
)

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
    case, to the people of the clinic that sent it, and to whoever holds
    a role in the destination laboratory.
    """

    if not user.is_authenticated or is_blocked(user):
        return False

    if user.is_superuser:
        return True

    if dental_case.created_by_id == user.id:
        return True

    if (
        dental_case.clinic_id is not None
        and dental_case.clinic.users.filter(pk=user.pk).exists()
    ):
        return True

    return can_in(
        user,
        Operation.VIEW_CASES,
        dental_case.laboratory,
    )


def filter_accessible_cases(user, cases):
    """
    Narrows a queryset to the dental cases the user may see.

    It is the queryset form of can_access_case: both must grant
    access to exactly the same cases.
    """

    if not user.is_authenticated or is_blocked(user):
        return cases.none()

    if user.is_superuser:
        return cases

    laboratories = get_laboratories(
        user,
        Operation.VIEW_CASES,
    )

    return cases.filter(
        Q(created_by=user)
        | Q(clinic__users=user)
        | Q(laboratory__in=laboratories)
    ).distinct()


def require_case_access(user, dental_case):
    """
    Raises PermissionDenied when the user may not access the case.
    """

    if not can_access_case(user, dental_case):
        raise PermissionDenied(ACCESS_DENIED_MESSAGE)


MANAGEMENT_DENIED_MESSAGE = (
    "You are not authorized to manage this laboratory case."
)

PRODUCTION_DENIED_MESSAGE = (
    "You are not authorized to update the production of this case."
)


def can_manage_case(user, dental_case):
    """
    Returns whether the user may run the laboratory's side of a case:
    accept or reject it, assign technicians and move it forward.
    """

    return can_in(
        user,
        Operation.MANAGE_CASES,
        dental_case.laboratory,
    )


def can_modify_case(user, dental_case):
    """
    Returns whether the user may edit or delete a dental case.

    Only the account that submitted it and whoever manages cases in
    its laboratory can: being able to see a case is not enough.
    """

    if not user.is_authenticated or is_blocked(user):
        return False

    if user.is_superuser:
        return True

    if dental_case.created_by_id == user.id:
        return True

    return can_manage_case(user, dental_case)


def can_update_production(user, dental_case):
    """
    Returns whether the user may record the production progress of a case.
    """

    return can_in(
        user,
        Operation.UPDATE_PRODUCTION,
        dental_case.laboratory,
    )


def require_case_management(user, dental_case):
    """
    Raises PermissionDenied when the user may not manage the case.
    """

    if not can_manage_case(user, dental_case):
        raise PermissionDenied(MANAGEMENT_DENIED_MESSAGE)


def require_production_update(user, dental_case):
    """
    Raises PermissionDenied when the user may not update the production.
    """

    if not can_update_production(user, dental_case):
        raise PermissionDenied(PRODUCTION_DENIED_MESSAGE)
