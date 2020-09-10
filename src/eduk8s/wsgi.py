"""
WSGI config for eduk8s project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

# This monkey patch allows setting of SameSite to 'None' while wait for
# Django 3.1 to catch up and release fix which sets it.

import wrapt

@wrapt.patch_function_wrapper("django.http.response", "HttpResponseBase.set_cookie")
def _wrapper_set_cookie(wrapped, instance, args, kwargs):
    samesite = None

    if "samesite" in kwargs:
        if kwargs.get("samesite") == "None":
            samesite = "None"
            kwargs["samesite"] = None

    result = wrapped(*args, **kwargs)

    if samesite:
        instance.cookies[args[0]]["samesite"] = samesite

    return result

# Normal Django WSGI application entrypoint.

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduk8s.settings')

application = get_wsgi_application()

# Initialize main loop for workshop manager background thread.

import workshops.manager

workshops.manager.initialize()
