"""Defines view handlers for listing available workshops via the web
interface and REST API.

"""

__all__ = ["catalog", "catalog_environments"]

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.utils.http import urlencode
from django.http import JsonResponse
from django.conf import settings

from oauth2_provider.decorators import protected_resource

from ..models import TrainingPortal, Environment, Session


def catalog(request):
    """Renders the list of workshops available in web interface."""

    index_url = request.session.get("index_url")

    if index_url:
        return redirect(index_url)

    if not request.user.is_staff and settings.PORTAL_INDEX:
        return redirect(settings.PORTAL_INDEX)

    entries = []

    notification = request.GET.get("notification", "")

    for environment in Environment.objects.all().order_by("name"):
        details = {}
        details["environment"] = environment.name
        details["workshop"] = environment.workshop

        capacity = max(0, environment.capacity - environment.allocated_sessions_count())
        details["capacity"] = capacity

        details["session"] = None

        if notification != "session-deleted" and request.user.is_authenticated:
            details["session"] = environment.allocated_session_for_user(request.user)

        entries.append(details)

    context = {"catalog": entries, "notification": request.GET.get("notification", "")}

    return render(request, "workshops/catalog.html", context)


if settings.CATALOG_VISIBILITY != "public":
    catalog = login_required(catalog)


def permit_access_to_event(handler):
    """Redirects to view handler presenting form to provide access token for
    accessing workshops via the training portal.

    """

    def _check_access_permitted(request):
        if not request.session.get("is_allowed_access_to_event"):
            return redirect(
                reverse("workshops_access")
                + "?"
                + urlencode({"redirect_url": reverse("workshops_catalog")})
            )
        return handler(request)

    return _check_access_permitted


if settings.PORTAL_PASSWORD:
    catalog = permit_access_to_event(catalog)


def catalog_environments(request):
    """Returns details of available workshops for REST API."""

    entries = []

    for environment in Environment.objects.all().order_by("name"):
        details = {}

        details["name"] = environment.name

        details["workshop"] = {
            "name": environment.workshop.name,
            "title": environment.workshop.title,
            "description": environment.workshop.description,
            "vendor": environment.workshop.vendor,
            "authors": environment.workshop.authors,
            "difficulty": environment.workshop.difficulty,
            "duration": environment.workshop.duration,
            "tags": environment.workshop.tags,
            "logo": environment.workshop.logo,
            "url": environment.workshop.url,
            "content": environment.workshop.content,
        }

        details["duration"] = int(environment.duration.total_seconds())

        details["capacity"] = environment.capacity
        details["reserved"] = environment.reserved

        details["allocated"] = environment.allocated_sessions_count()
        details["available"] = environment.available_sessions_count()

        entries.append(details)

    allocated_sessions = Session.allocated_sessions()

    portal_defaults = TrainingPortal.load()

    result = {
        "portal": {
            "name": settings.PORTAL_NAME,
            "url": f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}",
            "sessions": {
                "maximum": portal_defaults.sessions_maximum,
                "registered": portal_defaults.sessions_registered,
                "anonymous": portal_defaults.sessions_anonymous,
                "allocated": allocated_sessions.count(),
            },
        },
        "environments": entries,
    }

    return JsonResponse(result)


if settings.CATALOG_VISIBILITY != "public":
    catalog_environments = protected_resource()(catalog_environments)
