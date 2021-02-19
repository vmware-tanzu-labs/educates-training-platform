"""Defines view handlers for working with sessions via the web interface and
REST API.

"""

__all__ = [
    "session",
    "session_activate",
    "session_delete",
    "session_authorize",
    "session_schedule",
    "session_extend",
]

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    HttpResponseServerError,
)
from django.db import transaction
from django.contrib.auth import login
from django.http import JsonResponse
from django.conf import settings

from oauth2_provider.decorators import protected_resource

from csp.decorators import csp_update

from ..manager.locking import resources_lock
from ..manager.cleanup import delete_workshop_session
from ..manager.sessions import update_session_status
from ..models import TrainingPortal


@login_required
@resources_lock
@transaction.atomic
def session(request, name):
    """Renders the framed the workshop session."""

    context = {}

    index_url = request.session.get("index_url")

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    # Ensure there is allocated session for the user.

    instance = portal.allocated_session(name, request.user)

    if not instance:
        if index_url:
            return redirect(index_url + "?notification=session-invalid")

        if not request.user.is_staff and settings.PORTAL_INDEX:
            return redirect(settings.PORTAL_INDEX + "?notification=session-invalid")

        return redirect(reverse("workshops_catalog") + "?notification=session-invalid")

    context["session"] = instance
    context[
        "session_url"
    ] = f"{settings.INGRESS_PROTOCOL}://{instance.name}.{settings.INGRESS_DOMAIN}"

    response = render(request, "workshops/session.html", context)

    # This is abusing django-csp decorators in order to set a dynamic value
    # for connect-src and frame-src. Specifically, needs to be the hostname
    # of the users session.

    return csp_update(
        CONNECT_SRC=f"{instance.name}.{settings.INGRESS_DOMAIN}",
        FRAME_SRC=f"{instance.name}.{settings.INGRESS_DOMAIN}",
    )(lambda: response)()


def session_activate(request, name):
    """Activates the session spawned by an anonymous request via the
    web interface or REST API.

    """

    access_token = request.GET.get("token")
    index_url = request.GET.get("index_url")

    if not access_token:
        return HttpResponseBadRequest("No access token supplied")

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    instance = portal.allocated_session(name)

    if not instance:
        return HttpResponseBadRequest("Invalid session name supplied")

    if instance.token != access_token:
        return HttpResponseBadRequest("Invalid access token for session")

    if not instance.owner:
        return HttpResponseServerError("No owner defined for session")

    if not instance.owner.is_active:
        return HttpResponseServerError("Owner for session is not active")

    if not instance.is_running():
        update_session_status(instance.name, "Allocated")
        instance.mark_as_running()

    login(request, instance.owner, backend=settings.AUTHENTICATION_BACKENDS[0])

    request.session["index_url"] = index_url

    return redirect("workshops_session", name=instance.name)


@login_required(login_url="/")
@resources_lock
def session_delete(request, name):
    """Triggers deletion of a workshop session."""

    # Ensure there is allocated session for the user.

    index_url = request.session.get("index_url")

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    instance = portal.allocated_session(name, request.user)

    if not instance:
        if index_url:
            return redirect(index_url + "?notification=session-invalid")

        if not request.user.is_staff and settings.PORTAL_INDEX:
            return redirect(settings.PORTAL_INDEX + "?notification=session-invalid")

        return redirect(reverse("workshops_catalog") + "?notification=session-invalid")

    transaction.on_commit(lambda: delete_workshop_session(instance).schedule())

    if index_url:
        return redirect(index_url + "?notification=session-deleted")

    if not request.user.is_staff and settings.PORTAL_INDEX:
        return redirect(settings.PORTAL_INDEX + "?notification=session-deleted")

    return redirect(reverse("workshops_catalog") + "?notification=session-deleted")


@protected_resource()
def session_authorize(request, name):
    """Verifies that the user accessing a workshop session is permitted."""

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    # Ensure that the session exists.

    instance = portal.allocated_session(name)

    if not instance:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not instance.is_allocated():
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if instance.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    return JsonResponse({"owner": instance.owner.username})


@protected_resource()
def session_schedule(request, name):
    """Returns details about how long the workshop session is scheduled."""

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    # Ensure that the session exists.

    instance = portal.allocated_session(name)

    if not instance:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not instance.is_allocated():
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if instance.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    details = {}

    details["started"] = instance.started
    details["expires"] = instance.expires

    remaining = instance.time_remaining()

    if remaining is not None:
        details["countdown"] = remaining
        details["extendable"] = instance.is_extension_permitted()

    return JsonResponse(details)


@protected_resource()
def session_extend(request, name):
    """Extends the expiration time for the session where within the last
    period where extension is allowed.

    """

    # XXX What if the portal configuration doesn't exist as process
    # hasn't been initialized yet. Should return error indicating the
    # service is not available.

    portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)

    # Ensure that the session exists.

    instance = portal.allocated_session(name)

    if not instance:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not instance.is_allocated():
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if instance.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    # Session will only be extended if within the last period where extension
    # is allowed.

    instance.extend_time_remaining()

    details = {}

    details["started"] = instance.started
    details["expires"] = instance.expires

    remaining = instance.time_remaining()

    if remaining is not None:
        details["countdown"] = remaining
        details["extendable"] = instance.is_extension_permitted()

    return JsonResponse(details)
