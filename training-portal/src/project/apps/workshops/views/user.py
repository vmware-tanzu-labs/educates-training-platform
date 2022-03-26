"""Defines view handlers for determining details about users via the
REST API.

"""

__all__ = ["user_sessions"]

from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from oauth2_provider.decorators import protected_resource

from ..models import Environment


@protected_resource()
@require_http_methods(["GET"])
def user_sessions(request, name):
    """Returns list of workshop sessions user currently has active."""

    # Only allow user who is in the robots group to request details.

    if not request.user.groups.filter(name="robots").exists():
        return HttpResponseForbidden("Session requests not permitted")

    # Check that user asking about exists.

    User = get_user_model()  # pylint: disable=invalid-name

    try:
        user = User.objects.get(username=name)
    except User.DoesNotExist:
        return JsonResponse({"user": name, "sessions": []})

    sessions = []

    for environment in Environment.objects.all():
        session = environment.allocated_session_for_user(user)

        if session:
            details = {}

            details["name"] = session.name

            # The session namespace currently has the same name as the
            # session. Return it as a separate value in case it could be
            # different in the future.

            details["namespace"] = session.name

            details["workshop"] = session.workshop_name()
            details["environment"] = session.environment_name()

            details["started"] = session.started

            if session.expires:
                details["expires"] = session.expires

            remaining = session.time_remaining()

            if remaining is not None:
                details["countdown"] = remaining
                details["extendable"] = session.is_extension_permitted()

            sessions.append(details)

    result = {"user": name, "sessions": sessions}

    return JsonResponse(result)
