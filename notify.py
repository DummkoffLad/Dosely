# -*- coding: utf-8 -*-
"""Utilities para enviar notificaciones locales con repeticiones opcionales."""
import threading
from typing import Optional

from plyer import notification


class _RepeatingNotification:
    """Gestiona el envío periódico de una notificación."""

    def __init__(self, interval_seconds: float, title: str, message: str):
        self._interval = max(interval_seconds, 0)
        self._title = title
        self._message = message
        self._stop_event = threading.Event()
        self._timer: Optional[threading.Timer] = None

    def _dispatch(self):
        if self._stop_event.is_set():
            return
        send_notification(self._title, self._message)
        self._timer = threading.Timer(self._interval, self._dispatch)
        self._timer.daemon = True
        self._timer.start()

    def start(self):
        if self._interval <= 0:
            return
        self._timer = threading.Timer(self._interval, self._dispatch)
        self._timer.daemon = True
        self._timer.start()

    def cancel(self):
        self._stop_event.set()
        if self._timer:
            self._timer.cancel()


def send_notification(title: str, message: str):
    """Envía una notificación inmediata."""
    notification.notify(
        title=title,
        message=message,
        app_name="Dosely",
        timeout=5,
    )


def schedule_notification(delay: float, delay_unit: str, title: str, message: str, repeat: bool = False):
    """Programa una notificación diferida y opcionalmente repetitiva."""
    conversion_factors = {
        "hours": 3600,
        "days": 86400,
    }
    seconds = max(delay, 0) * conversion_factors.get(delay_unit, 1)

    if repeat:
        handler = _RepeatingNotification(seconds, title, message)
        handler.start()
        return handler

    timer = threading.Timer(seconds, send_notification, args=(title, message))
    timer.daemon = True
    timer.start()
    return timer