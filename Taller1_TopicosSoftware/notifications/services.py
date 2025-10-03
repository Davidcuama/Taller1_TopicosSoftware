"""
Observer pattern implementation for notifications.

This module defines a ``NotificationSubject`` that maintains a list of
``NotificationObserver`` objects.  When an event occurs (e.g. a resume
is accepted or rejected), the subject notifies all observers by
calling their ``notify`` method.  The concrete observer
``NotificationModelObserver`` creates a ``Notification`` record in the
database.  Additional observers (e.g., email or WebSocket
notifications) can be registered without changing the core logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from users.models import User
from .models import Notification


class NotificationObserver(ABC):
    """Interface for observers interested in notification events."""

    @abstractmethod
    def notify(self, user: User, message: str) -> None:
        """Receive a notification for a specific user."""


class NotificationSubject:
    """Subject that manages notification observers."""

    def __init__(self) -> None:
        self._observers: List[NotificationObserver] = []

    def register(self, observer: NotificationObserver) -> None:
        """Register an observer to receive notifications."""
        self._observers.append(observer)

    def unregister(self, observer: NotificationObserver) -> None:
        """Remove an observer from the notification list."""
        self._observers.remove(observer)

    def notify(self, user: User, message: str) -> None:
        """Notify all observers of an event for a particular user."""
        for observer in self._observers:
            observer.notify(user, message)


class NotificationModelObserver(NotificationObserver):
    """Observer that persists notifications to the database."""

    def notify(self, user: User, message: str) -> None:
        Notification.objects.create(user=user, message=message)


# Global subject instance used by the application
notification_subject = NotificationSubject()
# Register the model observer by default
notification_subject.register(NotificationModelObserver())