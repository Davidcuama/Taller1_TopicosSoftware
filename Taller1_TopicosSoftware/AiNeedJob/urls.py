"""
URL configuration for the AiNeedJob project.

This module maps URL paths to application URL configurations.  It delegates
to individual apps (`CVapp`, `offer`, and `users`) and serves media files
in development.  See Django documentation for details.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("CVapp.urls"), name="jobseeker"),
    path("offer/", include("offer.urls"), name="offer"),
    path("user/", include("users.urls"), name="user"),
    # Notifications routes: list and mark notifications for the current user
    path("notifications/", include("notifications.urls"), name="notifications"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)