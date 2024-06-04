import os
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

logging.basicConfig(level=logging.INFO)

logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logging.getLogger("kopf.activities.probe").setLevel(logging.WARNING)
logging.getLogger("kopf.objects").setLevel(logging.WARNING)

logger = logging.getLogger("educates")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

logger.info(
    "Logging level set to %s.", logging.getLevelName(logger.getEffectiveLevel())
)


# Normal Django WSGI application entrypoint.

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Initialize training portal operator.

from project.apps.workshops.manager.portal import initialize_portal

initialize_portal()
