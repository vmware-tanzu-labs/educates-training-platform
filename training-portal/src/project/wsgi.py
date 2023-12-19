import os
import logging


# Normal Django WSGI application entrypoint.

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# Initialize training portal operator.

logging.basicConfig(
        format="%(levelname)s:%(name)s - %(message)s", level=logging.INFO
    )

from project.apps.workshops.manager.portal import initialize_portal

initialize_portal()
