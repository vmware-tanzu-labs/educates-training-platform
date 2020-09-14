"""View handlers for workshops application.

"""

from .access import *
from .catalog import *
from .user import *


import os
import datetime
import random
import string
import uuid

import wrapt

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.http import JsonResponse
from django.utils import timezone
from django.utils.http import urlencode
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from oauth2_provider.views.generic import ProtectedResourceView
from oauth2_provider.decorators import protected_resource

from csp.decorators import csp_update

from ..models import TrainingPortal, Environment, Session, SessionState, Workshop
from ..manager import initiate_workshop_session, scheduler, retrieve_session_for_user
from ..forms import AccessTokenForm

portal_name = os.environ.get("TRAINING_PORTAL", "")

ingress_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
ingress_secret = os.environ.get("INGRESS_SECRET", "")
ingress_protocol = os.environ.get("INGRESS_PROTOCOL", "http")

portal_hostname = os.environ.get(
    "PORTAL_HOSTNAME", f"{portal_name}-ui.{ingress_domain}"
)
portal_password = os.environ.get("PORTAL_PASSWORD")
portal_index = os.environ.get("PORTAL_INDEX")

registration_type = os.environ.get("REGISTRATION_TYPE", "one-step")
enable_registration = os.environ.get("ENABLE_REGISTRATION", "true")
catalog_visibility = os.environ.get("CATALOG_VISIBILITY", "private")


@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def environment(request, name):
    context = {}

    index_url = request.session.get("index_url")

    # Ensure there is an environment with the specified name in existance.

    try:
        environment = Environment.objects.get(name=name)
    except Environment.DoesNotExist:
        if index_url:
            return redirect(index_url + "?notification=workshop-invalid")

        if not request.user.is_staff and portal_index:
            return redirect(portal_index + "?notification=workshop-invalid")

        return redirect(reverse("workshops_catalog") + "?notification=workshop-invalid")

    # Retrieve a session for the user for this workshop environment.

    session = retrieve_session_for_user(environment, request.user)

    if session:
        return redirect("workshops_session", name=session.name)

    if index_url:
        return redirect(index_url + "?notification=session-unavailable")

    if not request.user.is_staff and portal_index:
        return redirect(portal_index + "?notification=session-unavailable")

    return redirect(reverse("workshops_catalog") + "?notification=session-unavailable")


@wrapt.synchronized(scheduler)
@transaction.atomic
def environment_create(request, name):
    # Where the user is already authenticated, redirect immediately to
    # endpoint which actually triggers creation of environment. It will
    # validate if it is a correct environment name.

    if request.user.is_authenticated:
        return redirect("workshops_environment", name)

    # Where anonymous access is not enabled, need to redirect back to the
    # login page and they will need to first login.

    if enable_registration != "true" or registration_type != "anonymous":
        return redirect("login")

    # Is anonymous access, so we can login the user automatically.

    created = False

    while not created:
        username = f"anon@eduk8s:{uuid.uuid4()}"
        user, created = User.objects.get_or_create(username=username)

    group, _ = Group.objects.get_or_create(name="anonymous")

    user.groups.add(group)

    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

    # Finally redirect to endpoint which actually triggers creation of
    # environment. It will validate if it is a correct environment name.

    index_url = request.GET.get("index_url")

    request.session["index_url"] = index_url

    return redirect(reverse("workshops_environment", args=(name,)))


@protected_resource()
@wrapt.synchronized(scheduler)
@transaction.atomic
def environment_request(request, name):
    # Only allow user who is in the robots group to request session.

    if not request.user.groups.filter(name="robots").exists():
        return HttpResponseForbidden("Session requests not permitted")

    # Ensure there is an environment which the specified name in existance.

    try:
        environment = Environment.objects.get(name=name)
    except Environment.DoesNotExist:
        return HttpResponseForbidden("Environment does not exist")

    # Extract required parameters for creating the session. Check against
    # redirect_url, firstname and lastname is for backward compatibility
    # and will be removed in the future.

    index_url = request.GET.get("index_url")

    if not index_url:
        index_url = request.GET.get("redirect_url")

    if not index_url:
        return HttpResponseBadRequest("Need redirect URL for workshop index")

    user_id = request.GET.get("user", "").strip()

    if not user_id:
        user_id = uuid.uuid4()

    username = f"user@eduk8s:{user_id}"

    email = request.GET.get("email", "").strip()

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return HttpResponseBadRequest("Invalid email address provided")

    first_name = request.GET.get("first_name", "").strip()
    last_name = request.GET.get("last_name", "").strip()

    if not first_name:
        first_name = request.GET.get("firstname", "").strip()

    if not last_name:
        last_name = request.GET.get("lastname", "").strip()

    user_details = {}

    if email:
        user_details["email"] = email

    if first_name:
        user_details["first_name"] = first_name

    if last_name:
        user_details["last_name"] = last_name

    # Check whether a user already has an existing session allocated
    # to them, in which case return that rather than create a new one.

    session = None

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username, **user_details)
        group, _ = Group.objects.get_or_create(name="anonymous")
        user.groups.add(group)
        user.save()

    # Retrieve a session for the user for this workshop environment.

    characters = string.ascii_letters + string.digits
    token = "".join(random.sample(characters, 32))

    session = retrieve_session_for_user(environment, user, token)

    if not session:
        return JsonResponse({"error": "No session available"}, status=503)

    details = {}

    details["session"] = session.name
    details["user"] = user.username.split("user@eduk8s:")[-1]
    details["url"] = (
        reverse("workshops_session_activate", args=(session.name,))
        + "?"
        + urlencode({"token": session.token, "index_url": index_url})
    )

    return JsonResponse(details)


@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def session(request, name):
    context = {}

    index_url = request.session.get("index_url")

    # Ensure there is allocated session for the user.

    session = Session.allocated_session(name, request.user)

    if not session:
        if index_url:
            return redirect(index_url + "?notification=session-invalid")

        if not request.user.is_staff and portal_index:
            return redirect(portal_index + "?notification=session-invalid")

        return redirect(reverse("workshops_catalog") + "?notification=session-invalid")

    context["session"] = session
    context["session_url"] = f"{ingress_protocol}://{session.name}.{ingress_domain}"

    response = render(request, "workshops/session.html", context)

    # This is abusing django-csp decorators in order to set a dynamic value
    # for connect-src and frame-src. Specifically, needs to be the hostname
    # of the users session.

    return csp_update(
        CONNECT_SRC=f"{session.name}.{ingress_domain}",
        FRAME_SRC=f"{session.name}.{ingress_domain}",
    )(lambda: response)()


def session_activate(request, name):
    access_token = request.GET.get("token")
    index_url = request.GET.get("index_url")

    if not access_token:
        return HttpResponseBadRequest("No access token supplied")

    session = Session.allocated_session(name)

    if not session:
        return HttpResponseBadRequest("Invalid session name supplied")

    if session.token != access_token:
        return HttpResponseBadRequest("Invalid access token for session")

    if not session.owner:
        return HttpResponseServerError("No owner defined for session")

    if not session.owner.is_active:
        return HttpResponseServerError("Owner for session is not active")

    if session.state != SessionState.RUNNING:
        session.state = SessionState.RUNNING
        session.started = timezone.now()

        if session.environment.duration:
            session.expires = session.started + session.environment.duration
        else:
            session.expires = None

        session.save()

    login(request, session.owner, backend=settings.AUTHENTICATION_BACKENDS[0])

    request.session["index_url"] = index_url

    return redirect("workshops_session", name=session.name)


@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def session_delete(request, name):
    context = {}

    # Ensure there is allocated session for the user.

    index_url = request.session.get("index_url")

    session = Session.allocated_session(name, request.user)

    if not session:
        if index_url:
            return redirect(index_url + "?notification=session-invalid")

        if not request.user.is_staff and portal_index:
            return redirect(portal_index + "?notification=session-invalid")

        return redirect(reverse("workshops_catalog") + "?notification=session-invalid")

    scheduler.delete_workshop_session(session)

    if index_url:
        return redirect(index_url + "?notification=session-deleted")

        if not request.user.is_staff and portal_index:
            return redirect(portal_index + "?notification=session-deleted")

    return redirect(reverse("workshops_catalog") + "?notification=session-deleted")


@protected_resource()
def session_authorize(request, name):
    # Ensure that the session exists.

    session = Session.allocated_session(name)

    if not session:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not session.is_allocated():
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if session.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    return JsonResponse({"owner": session.owner.username})


@protected_resource()
def session_schedule(request, name):
    # Ensure that the session exists.

    session = Session.allocated_session(name)

    if not session:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not session.is_allocated():
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if session.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    details = {}

    details["started"] = session.started
    details["expires"] = session.expires

    if session.expires:
        now = timezone.now()
        if session.expires > now:
            details["countdown"] = int((session.expires - now).total_seconds())
        else:
            details["countdown"] = 0

    return JsonResponse(details)


@protected_resource()
def session_extend(request, name):
    # Ensure that the session exists.

    session = Session.allocated_session(name)

    if not session:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not session.is_allocated():
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if session.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    # Only extend if within the last five minutes and not already marked
    # for expiration. Extend for only an extra five minutes.

    if session.expires and session.state == SessionState.RUNNING:
        now = timezone.now()
        remaining = (session.expires - now).total_seconds()
        if remaining > 0 and remaining <= 300:
            session.expires = session.expires + datetime.timedelta(seconds=300)
            session.save()

    details = {}

    details["started"] = session.started
    details["expires"] = session.expires

    if session.expires:
        now = timezone.now()
        if session.expires > now:
            details["countdown"] = int((session.expires - now).total_seconds())
        else:
            details["countdown"] = 0

    return JsonResponse(details)
