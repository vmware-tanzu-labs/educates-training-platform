"""Defines view handlers for listing available workshops via the web
interface and REST API.

"""

__all__ = ["catalog", "catalog_environments"]

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.http import urlencode
from django.http import JsonResponse
from django.conf import settings

from oauth2_provider.decorators import protected_resource

from ..models import TrainingPortal, EnvironmentState, SessionState


@require_http_methods(["GET"])
def catalog(request):
    """Renders the list of workshops available in web interface."""

    index_url = request.session.get("index_url")

    if index_url:
        return redirect(index_url)

    if not request.user.is_staff and settings.PORTAL_INDEX:
        return redirect(settings.PORTAL_INDEX)

    entries = []

    notification = request.GET.get("notification", "")

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    for environment in portal.running_environments():
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


@require_http_methods(["GET"])
def catalog_environments(request):
    """Returns details of available workshops for REST API."""

    entries = []

    # If user is authenticated and a robot account, allow for inclusion
    # of sessions to be included.

    environment_states = []

    include_sessions = False

    if request.user.is_authenticated:
        if request.user.groups.filter(name="robots").exists():
            include_sessions = request.GET.get("sessions", "").lower() in (
                "true",
                "1",
            )

            include_states = map(str.lower, request.GET.getlist("state"))

            if "starting" in include_states:
                environment_states.append(EnvironmentState.STARTING)
            if "running" in include_states:
                environment_states.append(EnvironmentState.RUNNING)
            if "stopping" in include_states:
                environment_states.append(EnvironmentState.STOPPING)
            if "stopped" in include_states:
                environment_states.append(EnvironmentState.STOPPED)

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    if not environment_states:
        environment_states.append(EnvironmentState.RUNNING)

    for environment in portal.environments_in_state(environment_states):
        details = {}

        details["name"] = environment.name
        details["state"] = EnvironmentState(environment.state).name

        details["workshop"] = {
            "name": environment.workshop.name,
            "id": environment.workshop.content["id"],
            "title": environment.workshop.title,
            "description": environment.workshop.description,
            "vendor": environment.workshop.vendor,
            "authors": environment.workshop.authors,
            "difficulty": environment.workshop.difficulty,
            "duration": environment.workshop.duration,
            "tags": environment.workshop.tags,
            "logo": environment.workshop.logo,
            "url": environment.workshop.url,
        }

        details["duration"] = int(environment.expires.total_seconds())

        details["capacity"] = environment.capacity
        details["reserved"] = environment.reserved

        details["allocated"] = environment.allocated_sessions_count()
        details["available"] = environment.available_sessions_count()

        if include_sessions:
            sessions_data = []

            for session in environment.allocated_sessions():
                session_data = {
                    "name": session.name,
                    "state": SessionState(session.state).name,
                    "namespace": session.name,
                    "user": session.owner.username,
                    "started": session.started,
                }

                if session.expires:
                    session_data["expires"] = session.expires

                remaining = session.time_remaining()

                if remaining is not None:
                    session_data["countdown"] = remaining
                    session_data["extendable"] = session.is_extension_permitted()

                sessions_data.append(session_data)

            details["sessions"] = sessions_data

        entries.append(details)

    allocated_sessions = portal.allocated_sessions()

    result = {
        "portal": {
            "name": settings.TRAINING_PORTAL,
            "uid": portal.uid,
            "generation": portal.generation,
            "url": f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}",
            "sessions": {
                "maximum": portal.sessions_maximum,
                "registered": portal.sessions_registered,
                "anonymous": portal.sessions_anonymous,
                "allocated": allocated_sessions.count(),
            },
        },
        "environments": entries,
    }

    return JsonResponse(result)


if settings.CATALOG_VISIBILITY != "public":
    catalog_environments = protected_resource()(catalog_environments)
