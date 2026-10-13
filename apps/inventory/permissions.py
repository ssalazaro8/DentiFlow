def can_register_consumption(user, dental_case):
    """
    FR-13: quien puede registrar materiales de un caso.
    Superusuarios, tecnicos del laboratorio destino y el tecnico asignado.
    """

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    laboratory = dental_case.laboratory
    if laboratory is not None and laboratory.technicians.filter(pk=user.pk).exists():
        return True

    assignment = getattr(dental_case, "technician_assignment", None)
    return assignment is not None and assignment.technician_id == user.id