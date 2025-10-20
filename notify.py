# -*- coding: utf-8 -*-
"""
Módulo de notificaciones locales usando plyer.
- send_notification(title, message): notificación inmediata.
- schedule_notification(seconds, title, message): notificación retrasada.
"""
import threading
from plyer import notification


def send_notification(title: str, message: str):
    """
    Envía una notificación inmediata.
    """
    notification.notify(
        title=title,
        message=message,
        app_name="Dosely",
        timeout=5,  # segundos (algunas plataformas no respetan este valor)
    )


    

def schedule_notification(delay: float, delay_unit: str,title: str, message: str):
    """
    Programa el envío de una notificación después de 'seconds'.
    """
    conversion_factors = {

        'hours': 3600,
        'days': 86400,
    }
    seconds = delay * conversion_factors.get(delay_unit, 1)
    timer = threading.Timer(seconds, send_notification, args=(title, message))
    timer.daemon = True
    timer.start()
    return timer