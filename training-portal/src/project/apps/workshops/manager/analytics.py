import logging

import requests

from django.conf import settings
from django.utils import timezone

from .operator import background_task


@background_task
def send_event_to_webhook(url, message):
    try:
        requests.post(url, json=message)
    except Exception:
        logging.exception("Unable to report event to %s: %s", url, message)


def report_analytics_event(entity, event, data={}):
    message = None

    if not settings.ANALYTICS_WEBHOOK_URL:
        return

    if event.startswith("User/"):
        user = entity

        message = {
            "portal": {
                "name": settings.TRAINING_PORTAL,
                "url": f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}",
            },
            "event": {
                "name": event,
                "timestamp": timezone.now().isoformat(),
                # Not sure why in this case need to convert to string.
                "user": str(user.get_username()),
                "data": data,
            },
        }

    elif event.startswith("Environment/"):
        environment = entity

        portal = environment.portal

        message = {
            "portal": {
                "name": settings.TRAINING_PORTAL,
                "uid": portal.uid,
                "generation": portal.generation,
                "url": f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}",
            },
            "event": {
                "name": event,
                "timestamp": timezone.now().isoformat(),
                "environment": environment.name,
                "workshop": environment.workshop_name,
                "data": data,
            },
        }

    else:
        session = entity

        portal = session.environment.portal

        message = {
            "portal": {
                "name": settings.TRAINING_PORTAL,
                "uid": portal.uid,
                "generation": portal.generation,
                "url": f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}",
            },
            "event": {
                "name": event,
                "timestamp": timezone.now().isoformat(),
                "user": session.owner and session.owner.get_username() or None,
                "session": session.name,
                "environment": session.environment_name(),
                "workshop": session.workshop_name(),
                "data": data,
            },
        }

    if message:
        send_event_to_webhook(settings.ANALYTICS_WEBHOOK_URL, message).schedule()
