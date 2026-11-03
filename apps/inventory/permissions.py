from apps.accounts.permissions import Operation, can, can_in, is_blocked


def can_register_consumption(user, dental_case):
    """
    FR-13: quien puede registrar materiales de un caso.
    Superusuarios, quien registra la produccion en el laboratorio
    destino (FR-16) y el tecnico asignado.
    """

    if not user.is_authenticated or is_blocked(user):
        return False

    if user.is_superuser:
        return True

    if can_in(user, Operation.UPDATE_PRODUCTION, dental_case.laboratory):
        return True

    assignment = getattr(dental_case, "technician_assignment", None)
    return assignment is not None and assignment.technician_id == user.id


def can_view_consumption_report(user):
    """
    Quien puede revisar el consumo de materiales: superusuarios y
    el administrador del laboratorio, que es quien ve los reportes (FR-16).
    """

    return can(user, Operation.VIEW_REPORTS)
