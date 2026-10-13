from django import template

from apps.dental_cases.models import DentalCase

from ..forms import MaterialConsumptionForm
from ..permissions import can_register_consumption
from ..selectors import MaterialConsumptionSelector

register = template.Library()


@register.inclusion_tag(
    "inventory/includes/material_consumption_panel.html",
    takes_context=True,
)
def material_consumption_panel(context, dental_case):
    """FR-13: panel de materiales consumidos dentro del detalle del caso."""

    request = context["request"]
    can_register = (
        dental_case.status == DentalCase.Status.IN_PROGRESS
        and can_register_consumption(request.user, dental_case)
    )

    return {
        "dental_case": dental_case,
        "consumptions": MaterialConsumptionSelector.for_case(dental_case),
        "can_register": can_register,
        "form": MaterialConsumptionForm() if can_register else None,
        "csrf_token": context.get("csrf_token"),
    }