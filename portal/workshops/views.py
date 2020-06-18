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

from .models import Environment, Session, SessionState, Workshop
from .manager import initiate_workshop_session, scheduler

portal_name = os.environ.get("TRAINING_PORTAL", "")

ingress_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
ingress_secret = os.environ.get("INGRESS_SECRET", "")
ingress_protocol = os.environ.get("INGRESS_PROTOCOL", "http")

portal_hostname = os.environ.get("PORTAL_HOSTNAME", f"{portal_name}-ui.{ingress_domain}")

registration_type = os.environ.get('REGISTRATION_TYPE', 'one-step')
enable_registration = os.environ.get('ENABLE_REGISTRATION', 'true')
catalog_visibility = os.environ.get('CATALOG_VISIBILITY', 'private')

def catalog(request):
    index_url = request.session.get('index_url')

    if index_url:
        return redirect(index_url)

    catalog = []

    notification = request.GET.get('notification', '')

    for environment in Environment.objects.all().order_by('name'):
        details = {}
        details['environment'] = environment.name
        details['workshop'] = environment.workshop

        capacity = max(0, environment.capacity - environment.allocated_sessions_count())
        details['capacity'] = capacity

        details['session'] = None

        if notification != "session-deleted" and request.user.is_authenticated:
            details['session'] = environment.allocated_session_for_user(request.user)

        catalog.append(details)

    context = {
        "catalog": catalog,
        "notification": request.GET.get('notification', '')
    }

    return render(request, 'workshops/catalog.html', context)

if catalog_visibility != "public":
    catalog = login_required(catalog)

def catalog_environments(request):
    catalog = []

    for environment in Environment.objects.all().order_by('name'):
        details = {}

        details['name'] = environment.name

        details['workshop'] = {
            'name': environment.workshop.name,
            'title': environment.workshop.title,
            'description': environment.workshop.description,
            'vendor': environment.workshop.vendor,
            'authors': environment.workshop.authors,
            'difficulty': environment.workshop.difficulty,
            'duration': environment.workshop.duration,
            'tags': environment.workshop.tags,
            'logo': environment.workshop.logo,
            'url': environment.workshop.url,
            'content': environment.workshop.content,
        }

        details['duration'] = int(environment.duration.total_seconds())

        details['capacity'] = environment.capacity
        details['reserved'] = environment.reserved

        details['allocated'] = environment.allocated_sessions_count()
        details['available'] = environment.available_sessions_count()

        catalog.append(details)

    result = {
        "portal": {
            "name": portal_name,
            "url": f"{ingress_protocol}://{portal_hostname}",
        },
        "environments": catalog
    }

    return JsonResponse(result)

if catalog_visibility != "public":
    catalog_environments = protected_resource()(catalog_environments)

@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def environment(request, name):
    context = {}

    index_url = request.session.get('index_url')

    # Ensure there is an environment which the specified name in existance.

    try:
         environment = Environment.objects.get(name=name)
    except Environment.DoesNotExist:
        if index_url:
            return redirect(index_url+'?notification=workshop-invalid')

        return redirect(reverse('workshops_catalog')+'?notification=workshop-invalid')

    # Determine if there is already an allocated session which the current
    # user is an owner of.

    session = environment.allocated_session_for_user(request.user)

    if not session:
        # Allocate a session by getting all the sessions which have not
        # been allocated and allocate one.

        sessions = environment.available_sessions()

        if sessions:
            session = sessions[0]

            session.owner = request.user
            session.started = timezone.now()
            session.state = SessionState.RUNNING

            if environment.duration:
                session.expires = session.started + environment.duration

            # If required to have spare workshop instance, unless we
            # have reached capacity, initiate creation of a new session
            # to replace the one we just allocated.

            if environment.reserved and sessions.count()-1 < environment.reserved:
                if environment.active_sessions_count() < environment.capacity:
                    replacement_session = initiate_workshop_session(environment)

                    transaction.on_commit(lambda: scheduler.create_workshop_session(
                            name=replacement_session.name))

            session.save()

        else:
            # No session available. If there is still capacity,
            # then initiate creation of a new session and use it. We
            # shouldn't really get here if required to have spare
            # workshop instances unless capacity had been reached as
            # the spares should always have been topped up.

            if environment.active_sessions_count() < environment.capacity:
                expires = None

                now = timezone.now()

                if environment.duration:
                    expires = now + environment.duration

                session = initiate_workshop_session(environment,
                        owner=request.user, started=now, expires=expires)

                transaction.on_commit(lambda: scheduler.create_workshop_session(
                        name=session.name))

                session.save()
                environment.save()

    if session:
        return redirect('workshops_session', name=session.name)

    if index_url:
        return redirect(index_url+'?notification=session-unavailable')

    return redirect(reverse('workshops_catalog')+'?notification=session-unavailable')

def environment_create(request, name):
    # Where the user is already authenticated, redirect immediately to
    # endpoint which actually triggers creation of environment. It will
    # validate if it is a correct environment name.

    if request.user.is_authenticated:
        return redirect('workshops_environment', name)

    # Where anonymous access is not enabled, need to redirect back to the
    # login page and they will need to first login.

    if enable_registration != 'true' or registration_type != 'anonymous':
        return redirect('login')

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

    index_url = request.GET.get('index_url')

    request.session["index_url"] = index_url

    return redirect(reverse('workshops_environment', args=(name,)))

@protected_resource()
@wrapt.synchronized(scheduler)
@transaction.atomic
def environment_request(request, name):
    # Only allow user who is staff to request session.

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

    index_url = request.GET.get('index_url')

    if not index_url:
        index_url = request.GET.get('redirect_url')

    if not index_url:
        return HttpResponseBadRequest("Need redirect URL for workshop index")

    user_id = request.GET.get('user', '').strip()

    if not user_id:
        user_id = uuid.uuid4()

    username = f"user@eduk8s:{user_id}"

    email = request.GET.get('email', '').strip()

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return HttpResponseBadRequest("Invalid email address provided")

    first_name = request.GET.get('first_name', '').strip()
    last_name = request.GET.get('last_name', '').strip()

    if not first_name:
        first_name = request.GET.get('firstname', '').strip()

    if not last_name:
        last_name = request.GET.get('lastname', '').strip()

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
        user = None

    if user:
        session = environment.allocated_session_for_user(user)

    if session:
        details = {}

        details["session"] = session.name
        details["user"] = user.username.split('user@eduk8s:')[-1]

        if session.state != SessionState.RUNNING:
            session.expires = timezone.now() + datetime.timedelta(seconds=60)
            session.save()

        details["url"] = reverse('workshops_session_activate',
                args=(session.name,))+"?"+urlencode({"token":session.token,
                "index_url":index_url})

        return JsonResponse(details)

    # Allocate a session by getting all the sessions which have not
    # been allocated and allocate one.

    characters = string.ascii_letters + string.digits
    access_token = "".join(random.sample(characters, 32))

    sessions = environment.available_sessions()

    if sessions:
        session = sessions[0]

        if not user:
            user = User.objects.create_user(username, **user_details)
            group, _ = Group.objects.get_or_create(name="anonymous")
            user.groups.add(group)
            user.save()

        session.owner = user
        session.token = access_token
        session.started = timezone.now()

        session.expires = session.started + datetime.timedelta(seconds=60)

        # If required to have spare workshop instance, unless we
        # have reached capacity, initiate creation of a new session
        # to replace the one we just allocated.

        if environment.reserved and sessions.count()-1 < environment.reserved:
            if environment.active_sessions_count() < environment.capacity:
                replacement_session = initiate_workshop_session(environment)

                transaction.on_commit(lambda: scheduler.create_workshop_session(
                        name=replacement_session.name))

        session.save()

    else:
        # No session available. If there is still capacity,
        # then initiate creation of a new session and use it. We
        # shouldn't really get here if required to have spare
        # workshop instances unless capacity had been reached as
        # the spares should always have been topped up.

        if environment.active_sessions_count() < environment.capacity:
            now = timezone.now()
            expires = now + datetime.timedelta(seconds=60)

            if not user:
                user = User.objects.create_user(username, **user_details)
                group, _ = Group.objects.get_or_create(name="anonymous")
                user.groups.add(group)
                user.save()

            session = initiate_workshop_session(environment,
                    owner=user, token=access_token, redirect=index_url,
                    started=now, expires=expires)

            transaction.on_commit(lambda: scheduler.create_workshop_session(
                    name=session.name))

            session.save()
            environment.save()

        else:
            return JsonResponse({"error": "No session available"})

    details = {}

    details["session"] = session.name
    details["user"] = user.username.split('user@eduk8s:')[-1]
    details["url"] = reverse('workshops_session_activate',
            args=(session.name,))+"?"+urlencode({"token":session.token,
            "index_url":index_url})

    return JsonResponse(details)

@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def session(request, name):
    context = {}

    index_url = request.session.get('index_url')

    # Ensure there is allocated session for the user.

    session = Session.allocated_session(name, request.user)

    if not session:
        if index_url:
            return redirect(index_url+'?notification=session-invalid')

        return redirect(reverse('workshops_catalog')+'?notification=session-invalid')

    context['session'] = session
    context['session_url'] = f'{ingress_protocol}://{session.name}.{ingress_domain}'

    return render(request, 'workshops/session.html', context)

def session_activate(request, name):
    access_token = request.GET.get('token')
    index_url = request.GET.get('index_url')

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

    return redirect('workshops_session', name=session.name)

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
            return redirect(index_url+'?notification=session-invalid')

        return redirect(reverse('workshops_catalog')+'?notification=session-invalid')

    scheduler.delete_workshop_session(session)

    if index_url:
        return redirect(index_url+'?notification=session-deleted')

    return redirect(reverse('workshops_catalog')+'?notification=session-deleted')

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
