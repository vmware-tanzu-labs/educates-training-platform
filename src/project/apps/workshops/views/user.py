"""Defines view handlers for determining details about users via the
REST API.

"""

__all__ = ["user_sessions"]

from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone

from oauth2_provider.decorators import protected_resource

from ..models import Environment


@protected_resource()
def user_sessions(request, name):
    """Returns list of workshop sessions user currently has active."""

    # Only allow user who is in the robots group to request details.

    if not request.user.groups.filter(name="robots").exists():
        return HttpResponseForbidden("Session requests not permitted")

    # Check that user asking about exists.

    username = f"user@eduk8s:{name}"

    User = get_user_model() # pylint: disable=invalid-name

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"user": name, "sessions": []})

    sessions = []

    for environment in Environment.objects.all():
        session = environment.allocated_session_for_user(user)

        if session:
            details = {}

            details["name"] = session.name

            details["workshop"] = session.workshop_name()
            details["environment"] = session.environment_name()

            details["started"] = session.started
            details["expires"] = session.expires

            if session.expires:
                now = timezone.now()
                if session.expires > now:
                    details["countdown"] = int((session.expires - now).total_seconds())
                else:
                    details["countdown"] = 0

            sessions.append(details)

    result = {"user": name, "sessions": sessions}

    return JsonResponse(result)
