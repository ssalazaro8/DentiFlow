from django import template
from datetime import timedelta

register = template.Library()


@register.filter
def format_elapsed_time(delta):
    """
    Formatea un timedelta mostrando días, horas y minutos de forma legible.
    Ejemplo: 2d 5h 30m
    """
    if not isinstance(delta, timedelta):
        return ""

    total_seconds = int(delta.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    if not parts:
        return "< 1m"

    return " ".join(parts)
