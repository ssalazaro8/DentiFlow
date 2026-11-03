from django import template

from ..selectors import NotificationSelector

register = template.Library()


@register.inclusion_tag("notifications/includes/bell.html", takes_context=True)
def notification_bell(context):
    """FR-12: enlace del menu con el numero de avisos sin leer."""

    request = context.get("request")
    user = getattr(request, "user", None)

    unread_count = 0
    if user is not None and user.is_authenticated:
        unread_count = NotificationSelector.unread_count(user)

    return {
        "unread_count": unread_count,
        "path": request.path if request is not None else "",
    }