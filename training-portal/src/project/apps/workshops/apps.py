"""Django application objects.

"""

from django.apps import AppConfig


class WorkshopsConfig(AppConfig):
    """Config for workshops application."""

    name = "project.apps.workshops"
    default_auto_field = "django.db.models.AutoField"
