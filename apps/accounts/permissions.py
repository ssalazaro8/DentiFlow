"""
Roles and the operations each one may perform (FR-16).

The role of a person lives in their laboratory membership
(apps.users.LaboratoryUser) or, for the people of a dental clinic, in
the clinic they belong to. Every module asks here before a protected
operation, so the rule cannot diverge between screens.
"""

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from apps.clinics.models import Clinic
from apps.laboratories.models import Laboratory
from apps.users.models import LaboratoryUser


class Role:
    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    TECHNICIAN = "TECHNICIAN"
    # The people of a dental clinic: they send cases and follow them.
    CLINIC = "CLINIC"


class Operation:
    # Send a new dental case to a laboratory.
    CREATE_CASES = "create_cases"
    # See the laboratory's cases, their files and their tracking.
    VIEW_CASES = "view_cases"
    # Accept or reject cases, assign technicians and move them forward.
    MANAGE_CASES = "manage_cases"
    # Record the progress of a case through the workflow stages.
    UPDATE_PRODUCTION = "update_production"
    MANAGE_INVENTORY = "manage_inventory"
    VIEW_REPORTS = "view_reports"
    # Configure the laboratory's sequence of workflow stages.
    CONFIGURE_LABORATORY = "configure_laboratory"
    MANAGE_USERS = "manage_users"


ROLE_OPERATIONS = {
    Role.ADMIN: {
        Operation.CREATE_CASES,
        Operation.VIEW_CASES,
        Operation.MANAGE_CASES,
        Operation.UPDATE_PRODUCTION,
        Operation.MANAGE_INVENTORY,
        Operation.VIEW_REPORTS,
        Operation.CONFIGURE_LABORATORY,
        Operation.MANAGE_USERS,
    },
    Role.RECEPTIONIST: {
        Operation.CREATE_CASES,
        Operation.VIEW_CASES,
        Operation.MANAGE_CASES,
    },
    Role.TECHNICIAN: {
        Operation.VIEW_CASES,
        Operation.UPDATE_PRODUCTION,
        Operation.MANAGE_INVENTORY,
    },
    # A clinic sees its own cases through the case rules, not through
    # a laboratory, so creating cases is its only operation here.
    Role.CLINIC: {
        Operation.CREATE_CASES,
    },
}

# Accounts with neither a laboratory nor a clinic only send their own
# cases and follow them.
REQUESTER_OPERATIONS = {
    Operation.CREATE_CASES,
}

# Operations that do not happen inside one laboratory.
GLOBAL_OPERATIONS = {
    Operation.CREATE_CASES,
}

ACTIVE = "ACTIVE"

ACCESS_DENIED_MESSAGE = (
    "Your role does not allow this operation."
)

INACTIVE_ACCOUNT_MESSAGE = (
    "Your laboratory account is inactive."
)


def get_membership(user):
    """
    Returns the laboratory membership linked to the account, if any.
    """

    if not user.is_authenticated:
        return None

    return (
        LaboratoryUser.objects
        .select_related("laboratory")
        .filter(user=user)
        .first()
    )


def is_blocked(user):
    """
    Returns whether the account belongs to an inactive laboratory user.

    An inactive laboratory user keeps the account but may not perform
    any protected operation.
    """

    if not user.is_authenticated or user.is_superuser:
        return False

    membership = get_membership(user)

    return membership is not None and membership.status != ACTIVE


def get_role(user, laboratory):
    """
    Returns the role the user holds in a laboratory, or None.

    Accounts created before roles existed have no membership. They keep
    the access they already had through the laboratory's own lists: its
    authorized users act as administrators and its technicians as
    technicians.
    """

    if not user.is_authenticated or laboratory is None:
        return None

    if user.is_superuser:
        return Role.ADMIN

    membership = get_membership(user)

    if membership is not None:

        if membership.status != ACTIVE:
            return None

        if membership.laboratory_id != laboratory.pk:
            return None

        return membership.role

    if laboratory.authorized_users.filter(pk=user.pk).exists():
        return Role.ADMIN

    if laboratory.technicians.filter(pk=user.pk).exists():
        return Role.TECHNICIAN

    return None


def get_laboratories(user, operation):
    """
    Returns the laboratories where the user may perform an operation.
    """

    if not user.is_authenticated:
        return Laboratory.objects.none()

    if user.is_superuser:
        return Laboratory.objects.all()

    membership = get_membership(user)

    if membership is not None:

        allowed = (
            membership.status == ACTIVE
            and operation in ROLE_OPERATIONS.get(membership.role, ())
        )

        if not allowed:
            return Laboratory.objects.none()

        return Laboratory.objects.filter(pk=membership.laboratory_id)

    condition = Q(authorized_users=user)

    if operation in ROLE_OPERATIONS[Role.TECHNICIAN]:
        condition |= Q(technicians=user)

    return Laboratory.objects.filter(condition).distinct()


def get_clinic(user):
    """
    Returns the clinic the account belongs to, if any.
    """

    if not user.is_authenticated:
        return None

    return Clinic.objects.filter(users=user).first()


def get_home(user):
    """
    Returns the laboratory the user works for and their role in it.

    The people of a clinic get no laboratory and the clinic role. Both
    are None for accounts that belong to neither.
    """

    if not user.is_authenticated:
        return None, None

    if user.is_superuser:
        return Laboratory.objects.first(), Role.ADMIN

    membership = get_membership(user)

    if membership is not None:

        if membership.status != ACTIVE or membership.laboratory is None:
            return None, None

        return membership.laboratory, membership.role

    laboratory = Laboratory.objects.filter(authorized_users=user).first()

    if laboratory is not None:
        return laboratory, Role.ADMIN

    laboratory = Laboratory.objects.filter(technicians=user).first()

    if laboratory is not None:
        return laboratory, Role.TECHNICIAN

    if get_clinic(user) is not None:
        return None, Role.CLINIC

    return None, None


def can(user, operation):
    """
    Returns whether the user may perform an operation in the laboratory
    they work for.
    """

    if not user.is_authenticated or is_blocked(user):
        return False

    if user.is_superuser:
        return True

    if operation in GLOBAL_OPERATIONS:

        laboratory, role = get_home(user)

        if role is None:
            return operation in REQUESTER_OPERATIONS

        return operation in ROLE_OPERATIONS[role]

    return get_laboratories(user, operation).exists()


def can_in(user, operation, laboratory):
    """
    Returns whether the user may perform an operation in one laboratory.
    """

    role = get_role(user, laboratory)

    return operation in ROLE_OPERATIONS.get(role, ())


def require(user, operation, laboratory=None):
    """
    Raises PermissionDenied when the role does not allow the operation.

    With a laboratory, the role checked is the one held in it.
    """

    if laboratory is None:
        allowed = can(user, operation)
    else:
        allowed = can_in(user, operation, laboratory)

    if not allowed:
        raise PermissionDenied(ACCESS_DENIED_MESSAGE)


def can_view_clinic(user, clinic):
    """
    Returns whether the user may open the page of a clinic.

    The clinic's own people may, and so may whoever sees cases in a
    laboratory. The page itself only lists the cases the user can see.
    """

    if not user.is_authenticated or is_blocked(user):
        return False

    if user.is_superuser:
        return True

    if clinic.users.filter(pk=user.pk).exists():
        return True

    return can(user, Operation.VIEW_CASES)


def require_clinic_access(user, clinic):
    """
    Raises PermissionDenied when the user may not open the clinic page.
    """

    if not can_view_clinic(user, clinic):
        raise PermissionDenied(ACCESS_DENIED_MESSAGE)
