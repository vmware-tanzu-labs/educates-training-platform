import os
import datetime
import random
import string

import wrapt

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.conf import settings

from oauth2_provider.views.generic import ProtectedResourceView
from oauth2_provider.decorators import protected_resource

from .models import Environment, Session, Workshop
from .manager import initiate_workshop_session, scheduler

portal_name = os.environ.get("TRAINING_PORTAL", "")

ingress_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
ingress_secret = os.environ.get("INGRESS_SECRET", "")
ingress_protocol = os.environ.get("INGRESS_PROTOCOL", "http")

portal_hostname = os.environ.get("PORTAL_HOSTNAME", f"{portal_name}-ui.{ingress_domain}")

@login_required
def catalog(request):
    catalog = []

    notification = request.GET.get('notification', '')

    for environment in Environment.objects.all().order_by('name'):
        details = {}
        details['environment'] = environment.name
        details['workshop'] = environment.workshop

        available = max(0, environment.capacity - Session.objects.filter(
                environment=environment, allocated=True).count())
        details['available'] = available

        if notification != "session-deleted":
            sessions = environment.session_set.filter(allocated=True, owner=request.user)
            details['session'] = sessions and sessions[0] or None
        else:
            details['session'] = None

        catalog.append(details)

    context = {
        "catalog": catalog,
        "notification": request.GET.get('notification', '')
    }

    return render(request, 'workshops/catalog.html', context)

@protected_resource()
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
            'image': environment.workshop.image,
            'content': environment.workshop.content,
        }

        details['duration'] = environment.duration

        details['capacity'] = environment.capacity
        details['reserved'] = environment.reserved

        details['allocated'] = Session.objects.filter(environment=environment,
                allocated=True).count()
        details['available'] = Session.objects.filter(environment=environment,
                allocated=False).count()

        catalog.append(details)

    result = {
        "portal": {
            "name": portal_name,
            "url": f"{ingress_protocol}://{portal_hostname}",
        },
        "environments": catalog
    }

    return JsonResponse(result)

@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def environment(request, name):
    context = {}

    # Ensure there is an environment which the specified name in existance.

    try:
         environment = Environment.objects.get(name=name)
    except Environment.DoesNotExist:
        return redirect(reverse('workshops_catalog')+'?notification=workshop-invalid')

    # Determine if there is already an allocated session which the current
    # user is an owner of.

    session = None

    sessions = environment.session_set.filter(allocated=True, owner=request.user)

    if not sessions:
        # Allocate a session by getting all the sessions which have not
        # been allocated and allocate one.

        sessions = environment.session_set.filter(allocated=False)

        if sessions:
            session = sessions[0]

            session.owner = request.user
            session.allocated = True

            session.started = timezone.now()

            if environment.duration:
                session.expires = (session.started +
                        datetime.timedelta(seconds=environment.duration))

            # If required to have spare workshop instance, unless we
            # have reached capacity, initiate creation of a new session
            # to replace the one we just allocated.

            reserved_sessions = Session.objects.filter(environment=name,
                    allocated=False)

            if environment.reserved and reserved_sessions.count()-1 < environment.reserved:
                active_sessions = Session.objects.filter(environment=environment)

                if active_sessions.count() < environment.capacity:
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

            active_sessions = Session.objects.filter(environment=environment)

            if active_sessions.count() < environment.capacity:
                expires = None

                now = timezone.now()

                if environment.duration:
                    expires = now + datetime.timedelta(seconds=environment.duration)

                session = initiate_workshop_session(environment,
                        owner=request.user, allocated=True,
                        started=now, expires=expires)

                transaction.on_commit(lambda: scheduler.create_workshop_session(
                        name=session.name))

                session.save()
                environment.save()

    else:
        session = sessions[0]

    if session:
        return redirect('workshops_session', name=session.name)

    return redirect(reverse('workshops_catalog')+'?notification=session-unavailable')

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

    # Extract required parameters for creating the session.

    redirect_url = request.GET.get('redirect_url')

    if not redirect_url:
        return HttpResponseBadRequest("Need redirect URL for session end")

    # Allocate a session by getting all the sessions which have not
    # been allocated and allocate one.

    characters = string.ascii_letters + string.digits
    user_tag = "".join(random.sample(characters, 5))
    access_token = "".join(random.sample(characters, 32))

    sessions = environment.session_set.filter(allocated=False)

    if sessions:
        session = sessions[0]

        user = User.objects.create_user(f"{session.name}-{user_tag}")

        session.owner = user
        session.anonymous = True
        session.token = access_token
        session.redirect = redirect_url
        session.allocated = True

        session.started = timezone.now()
        session.expires = session.started + datetime.timedelta(seconds=60)

        # If required to have spare workshop instance, unless we
        # have reached capacity, initiate creation of a new session
        # to replace the one we just allocated.

        reserved_sessions = Session.objects.filter(environment=name,
                allocated=False)

        if environment.reserved and reserved_sessions.count()-1 < environment.reserved:
            active_sessions = Session.objects.filter(environment=environment)

            if active_sessions.count() < environment.capacity:
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

        active_sessions = Session.objects.filter(environment=environment)

        if active_sessions.count() < environment.capacity:
            now = timezone.now()
            expires = now + datetime.timedelta(seconds=60)

            session = initiate_workshop_session(environment,
                    anonymous=True, token=access_token,
                    redirect=redirect_url, allocated=True,
                    started=now, expires=expires)

            session.owner = User.objects.create_user(f"{session.name}-{user_tag}")

            transaction.on_commit(lambda: scheduler.create_workshop_session(
                    name=session.name))

            session.save()
            environment.save()

        else:
            return JsonResponse({"error": "No session available"})

    details = {}

    details["session"] = session.name
    details["url"] = reverse('workshops_session_activate',
            args=(session.name,))+f'?token={session.token}'

    return JsonResponse(details)

@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def session(request, name):
    context = {}

    # Ensure there is allocated session for the user.

    try:
        session = Session.objects.get(name=name, allocated=True,
                owner=request.user)
    except Session.DoesNotExist:
        return redirect(reverse('workshops_catalog')+'?notification=session-invalid')

    context['session'] = session
    context['session_url'] = f'{ingress_protocol}://{session.name}.{ingress_domain}'

    return render(request, 'workshops/session.html', context)

def session_activate(request, name):
    access_token = request.GET.get('token')

    if not access_token:
        return HttpResponseBadRequest("No access token supplied")

    try:
        session = Session.objects.get(name=name, allocated=True)
    except Session.DoesNotExist:
        return HttpResponseBadRequest("Invalid session name supplied")

    if session.token != access_token:
        return HttpResponseBadRequest("Invalid access token for session")

    if not session.owner:
        return HttpResponseServerError("No owner defined for session")

    if not session.owner.is_active:
        return HttpResponseServerError("Owner for session is not active")

    session.token = None

    session.started = timezone.now()

    if session.environment.duration:
        session.expires = (session.started +
                datetime.timedelta(seconds=session.environment.duration))
    else:
        session.expires = None

    session.save()

    login(request, session.owner, backend=settings.AUTHENTICATION_BACKENDS[0])

    return redirect('workshops_session', name=session.name)

@login_required
@wrapt.synchronized(scheduler)
@transaction.atomic
def session_delete(request, name):
    context = {}

    # Ensure there is allocated session for the user.

    try:
         session = Session.objects.get(name=name, allocated=True,
                 owner=request.user)
    except Session.DoesNotExist:
        return redirect(reverse('workshops_catalog')+'?notification=session-invalid')

    scheduler.delete_workshop_session(session)

    if session.redirect:
        return redirect(session.redirect)

    return redirect(reverse('workshops_catalog')+'?notification=session-deleted')

@protected_resource()
def session_authorize(request, name):
    # Ensure that the session exists.

    try:
         session = Session.objects.get(name=name)
    except Session.DoesNotExist:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not session.allocated:
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if session.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    return JsonResponse({"owner": session.owner.username})

@protected_resource()
def session_schedule(request, name):
    # Ensure that the session exists.

    try:
         session = Session.objects.get(name=name)
    except Session.DoesNotExist:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not session.allocated:
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
            details["countdown"] = int((session.expires-now).total_seconds())
        else:
            details["countdown"] = 0

    return JsonResponse(details)

@protected_resource()
def session_extend(request, name):
    # Ensure that the session exists.

    try:
         session = Session.objects.get(name=name)
    except Session.DoesNotExist:
        raise Http404("Session does not exist")

    # Check that session is allocated and in use.

    if not session.allocated:
        return HttpResponseForbidden("Session is not currently in use")

    # Check that are owner of session, or a staff member.

    if not request.user.is_staff:
        if session.owner != request.user:
            return HttpResponseForbidden("Access to session not permitted")

    # Only extend if within the last five miniutes. Extend
    # for only an extra five minutes.

    if session.expires:
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
            details["countdown"] = int((session.expires-now).total_seconds())
        else:
            details["countdown"] = 0

    return JsonResponse(details)
