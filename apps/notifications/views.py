from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification
from .selectors import NotificationSelector
from .services import NotificationService


@login_required
def notification_list(request):
    """FR-12: avisos pendientes del usuario y los ultimos ya leidos."""

    return render(
        request,
        "notifications/list.html",
        {
            "pending": NotificationSelector.pending_for_user(request.user),
            "recent_read": NotificationSelector.read_for_user(request.user)[:10],
        },
    )


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    # Solo se pueden marcar los avisos propios.
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient=request.user,
    )
    NotificationService.mark_as_read(notification)

    return redirect("notification_list")


@login_required
@require_POST
def notification_mark_all_read(request):
    count = NotificationService.mark_all_as_read(request.user)

    if count:
        messages.success(request, "All notifications marked as read.")

    return redirect("notification_list")