import logging

import requests

from datetime import datetime, timezone

from .operator_config import ANALYTICS_WEBHOOK_URL


logger = logging.getLogger("educates")


def current_time():
    dt = datetime.now(timezone.utc)
    tz_dt = dt.astimezone()
    return tz_dt.isoformat()


def send_event_to_webhook(url, message):
    try:
        requests.post(url, json=message, timeout=2.5)
    except Exception:
        logging.exception("Unable to report event to %s: %s", url, message)


def report_analytics_event(event, data={}):
    message = {
        "event": {
            "name": event,
            "timestamp": current_time(),
            "data": data,
        },
    }

    logger.debug("Reporting analytics event %s as message %s.", event, message)

    if not ANALYTICS_WEBHOOK_URL:
        return

    send_event_to_webhook(ANALYTICS_WEBHOOK_URL, message)
