import logging

import requests

from django.conf import settings
from django.utils import timezone

from .operator import background_task


@background_task
def send_event_to_webhook(url, data):
    try:
        requests.post(url, json=data)
    except Exception:
        logging.exception("Unable to report event to %s: %s", url, data)


def report_analytics_event(session, event):
    portal = session.environment.portal

    if not portal.analytics_url:
        return

    if not session.owner:
        return

    data = {
        "portal": {
            "name": settings.TRAINING_PORTAL,
            "uid": portal.uid,
            "generation": portal.generation,
            "url": f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}",
        },
        "event": {
            "name": event,
            "timestamp": timezone.now().isoformat(),
            "user": session.owner.username,
            "session": session.name,
            "environment": session.environment_name(),
            "workshop": session.workshop_name(),
        },
    }

    send_event_to_webhook(portal.analytics_url, data).schedule()
