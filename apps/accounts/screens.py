"""
Which operation each screen requires, the menu built from it and the
home page of each role (FR-16).

Only the screens whose access depends on the role alone are listed
here. Actions over one specific case check the role inside the view,
against the laboratory of that case.

The menu is built from the same table, so a link is shown only when
the screen behind it would let the user in.
"""

from django.urls import reverse

from apps.users.models import LaboratoryUser

from .permissions import Operation, Role, can, get_clinic, get_home

SCREEN_OPERATIONS = {
    "dashboard": Operation.VIEW_REPORTS,
    "dental_case_create": Operation.CREATE_CASES,
    "laboratory_case_inbox": Operation.VIEW_CASES,
    "clinic_list": Operation.VIEW_CASES,
    "clinic_create": Operation.MANAGE_USERS,
    "workflow_list": Operation.VIEW_CASES,
    "workflow_create": Operation.MANAGE_CASES,
    "material_list": Operation.MANAGE_INVENTORY,
    "material_update_stock": Operation.MANAGE_INVENTORY,
    "operational_reports": Operation.VIEW_REPORTS,
    "download_report": Operation.VIEW_REPORTS,
    "workflow_stage_list": Operation.CONFIGURE_LABORATORY,
    "workflow_stage_create": Operation.CONFIGURE_LABORATORY,
    "workflow_stage_edit": Operation.CONFIGURE_LABORATORY,
    "workflow_stage_toggle": Operation.CONFIGURE_LABORATORY,
    "workflow_stage_move": Operation.CONFIGURE_LABORATORY,
    "technician_create": Operation.MANAGE_USERS,
    "users:create": Operation.MANAGE_USERS,
}

# Who may see an entry: an operation, the clinic role, or everybody.
EVERYBODY = "everybody"
CLINIC_ONLY = "clinic"
# Clinics and accounts without a role: their case list is "List Cases",
# while the laboratory roles work from their laboratory's inbox.
OUTSIDE_LABORATORY = "outside_laboratory"

# label, icon, screen, who may see it, address argument, active prefix
# The address argument is "laboratory" or "clinic" when the screen
# belongs to the user's own laboratory or clinic.
MENU = [
    ("Dashboard", "fa-tachometer-alt", "dashboard", Operation.VIEW_REPORTS, None, "/cases/dashboard/"),
    (
        "Cases", "fa-file-medical", [
            ("List Cases", "fa-list", "dental_case_list", OUTSIDE_LABORATORY, None),
            ("Create Case", "fa-plus", "dental_case_create", Operation.CREATE_CASES, None),
            ("Laboratory Inbox", "fa-inbox", "laboratory_case_inbox", Operation.VIEW_CASES, "laboratory"),
        ],
        None, None, "/cases/",
    ),
    ("My Clinic", "fa-hospital", "clinic_detail", CLINIC_ONLY, "clinic", "/clinics/"),
    ("Clinics", "fa-hospital", "clinic_list", Operation.VIEW_CASES, None, "/clinics/"),
    ("Labs", "fa-flask", "laboratory_list", EVERYBODY, None, "/laboratories/"),
    ("Workflow", "fa-stream", "workflow_list", Operation.VIEW_CASES, None, "/workflow/"),
    ("Inventory", "fa-cubes", "material_list", Operation.MANAGE_INVENTORY, None, "/inventory/"),
    ("Reports", "fa-chart-bar", "operational_reports", Operation.VIEW_REPORTS, None, "/reports/"),
    (
        "Laboratory", "fa-cog", [
            ("Workflow Stages", "fa-list-ol", "workflow_stage_list", Operation.CONFIGURE_LABORATORY, "laboratory"),
            ("Register User", "fa-user-plus", "users:create", Operation.MANAGE_USERS, None),
        ],
        None, None, "/users/",
    ),
]

ROLE_LABELS = dict(LaboratoryUser.ROLE_CHOICES)
ROLE_LABELS[Role.CLINIC] = "Clinic"


def _is_active(label, prefix, path):
    """
    Returns whether a menu entry matches the page being shown.
    """

    stages = path.startswith("/workflow/laboratories/")

    if label == "Cases":
        return path.startswith(prefix) and not path.startswith("/cases/dashboard/")

    if label == "Workflow":
        return path.startswith(prefix) and not stages

    if label == "Laboratory":
        return path.startswith(prefix) or stages

    return path.startswith(prefix)


def _allowed(user, who, laboratory, clinic):

    if who == EVERYBODY:
        return True

    if who == CLINIC_ONLY:
        return clinic is not None and get_home(user)[1] == Role.CLINIC

    if who == OUTSIDE_LABORATORY:
        return user.is_superuser or not can(user, Operation.VIEW_CASES)

    return can(user, who)


def _address(screen, argument, laboratory, clinic):

    if argument == "laboratory":
        return None if laboratory is None else reverse(screen, args=[laboratory.pk])

    if argument == "clinic":
        return None if clinic is None else reverse(screen, args=[clinic.pk])

    return reverse(screen)


def build_menu(user, path=""):
    """
    Returns the menu entries the user may open.

    Each entry has a label, an icon, an address or a list of children,
    and whether it matches the page being shown.
    """

    laboratory, role = get_home(user)
    clinic = get_clinic(user)

    entries = []

    for label, icon, target, who, argument, prefix in MENU:

        if isinstance(target, list):

            children = []

            for child_label, child_icon, screen, child_who, child_argument in target:

                if not _allowed(user, child_who, laboratory, clinic):
                    continue

                address = _address(screen, child_argument, laboratory, clinic)

                if address is not None:
                    children.append(
                        {"label": child_label, "icon": child_icon, "url": address}
                    )

            if not children:
                continue

            entries.append(
                {
                    "label": label,
                    "icon": icon,
                    "children": children,
                    "active": _is_active(label, prefix, path),
                }
            )

            continue

        if not _allowed(user, who, laboratory, clinic):
            continue

        address = _address(target, argument, laboratory, clinic)

        if address is None:
            continue

        entries.append(
            {
                "label": label,
                "icon": icon,
                "url": address,
                "active": _is_active(label, prefix, path),
            }
        )

    return entries


def describe_role(user):
    """
    Returns the role of the user as shown next to their name.
    """

    if user.is_superuser:
        return "Superuser"

    laboratory, role = get_home(user)

    if role is None:
        return ""

    if role == Role.CLINIC:
        return f"Clinic · {get_clinic(user).name}"

    return f"{ROLE_LABELS.get(role, role)} · {laboratory.name}"


def home_url(user):
    """
    Returns the page each role starts on after signing in.
    """

    laboratory, role = get_home(user)

    if user.is_superuser or role == Role.ADMIN:
        return reverse("dashboard")

    if role == Role.RECEPTIONIST:
        return reverse("laboratory_case_inbox", args=[laboratory.pk])

    if role == Role.TECHNICIAN:
        return reverse("workflow_list")

    if role == Role.CLINIC:
        return reverse("clinic_detail", args=[get_clinic(user).pk])

    return reverse("dental_case_list")
