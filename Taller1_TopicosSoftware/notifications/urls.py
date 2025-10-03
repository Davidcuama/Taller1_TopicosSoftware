"""
URL patterns for the notifications app.

This module defines the routes for listing notifications and marking
individual notifications as read.  It is included in the project’s
root URL configuration under the ``notifications/`` prefix.
"""

from django.urls import path

from . import views


urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path(
        "mark/<int:notification_id>/", views.mark_notification_read, name="mark_notification_read"
    ),
]