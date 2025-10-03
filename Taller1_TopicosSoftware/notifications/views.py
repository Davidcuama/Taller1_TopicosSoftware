"""
Views for the notifications app.

This module exposes simple views to list notifications for the
authenticated user and to mark individual notifications as read.
It uses session‑based authentication (``request.session['user_id']``)
consistent with the rest of the project.

The Observer pattern implemented in ``notifications.services``
generates ``Notification`` entries whenever an event occurs (e.g.,
accepting or rejecting a resume).  These views allow end users to
inspect those notifications from the web interface.
"""

from __future__ import annotations

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from users.models import User
from .models import Notification


def notification_list(request):
    """Display a list of notifications for the logged‑in user.

    If no user is authenticated via the session, redirect to the
    login page.  Notifications are ordered from most recent to
    oldest.
    """
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    notifications = Notification.objects.filter(user=user).order_by("-created_at")
    return render(
        request,
        "notifications.html",
        {
            "notifications": notifications,
            "user": user,
        },
    )


def mark_notification_read(request, notification_id: int) -> object:
    """Mark a specific notification as read and redirect back to the list.

    Only allows the owner of the notification to mark it as read.  If a
    different user attempts to mark the notification, an error message
    is shown and they are redirected to the notifications list.
    """
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    notification = get_object_or_404(Notification, id=notification_id)
    if notification.user != user:
        messages.error(request, "No tienes permiso para modificar esta notificación.")
        return redirect("notification_list")
    if not notification.read:
        notification.read = True
        notification.save()
        messages.success(request, "Notificación marcada como leída.")
    return redirect("notification_list")