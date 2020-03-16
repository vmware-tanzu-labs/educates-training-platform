from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, JsonResponse

from oauth2_provider.views.generic import ProtectedResourceView

from .models import Environment, Session
from .manager import initiate_workshop_session

@login_required
def catalog(request):
    catalog = []

    for environment in Environment.objects.all().order_by('name'):
        details = {}
        details['environment'] = environment.name
        details['workshop'] = environment.workshop

        available = Session.objects.filter(environment=environment,
                allocated=False, state="running").count()
        details['available'] = available

        sessions = environment.session_set.filter(allocated=True, state="running", owner=request.user)
        details['session'] = sessions and sessions[0] or None

        catalog.append(details)

    context = {"catalog": catalog}

    return render(request, 'workshops/catalog.html', context)

@login_required
@transaction.atomic
def environment(request, environment):
    context = {}

    # Ensure there is an environment which the specified name in existance.

    try:
         selected = Environment.objects.get(name=environment)
    except Environment.DoesNotExist:
        raise Http404("Environment does not exist")

    # Determine if there is already an allocated session which the current
    # user is an owner of.

    session = None

    sessions = selected.session_set.filter(allocated=True, state="running", owner=request.user)

    if not sessions:
        # Allocate a session by getting all the sessions which have not
        # been allocated and allocate one.

        sessions = selected.session_set.filter(allocated=False, state="running")

        if sessions:
            session = sessions[0]

            session.owner = request.user
            session.allocated = True

            session.save()

            # If required to have spare workshop instance, unless we
            # have reached capacity, initiate creation of a new session
            # to replace the one we just allocated.

            if selected.reserved:
                active_sessions = Session.objects.filter(environment=selected,
                        state__in=["starting", "running"])

                if active_sessions.count() < selected.capacity:
                    initiate_workshop_session(selected)
                    selected.save()

        else:
            # No session available. If there there is still capacity,
            # then initiate creation of a new session and use it. We
            # shouldn't really get here if required to have spare
            # workshop instances unless capacity had been reached as
            # the spares should always have been topped up.

            active_sessions = Session.objects.filter(environment=selected,
                    state__in=["starting", "running"])

            if active_sessions.count() < selected.capacity:
                session = initiate_workshop_session(selected)

                session.owner = request.user
                session.allocated = True

                session.save()

                selected.save()

    else:
        session = sessions[0]

    if not session:
        return render(request, 'workshops/environment-unavailable.html')

    context['session'] = session
    context['session_url'] = f'http://{session.name}.{session.domain}'

    return render(request, 'workshops/environment.html', context)

class SessionAuthorizationEndpoint(ProtectedResourceView):
    def get(self, request, session):
        # Ensure that the session exists.

        try:
             selected = Session.objects.get(name=session)
        except Session.DoesNotExist:
            raise Http404("Session does not exist")

        # Check that session is allocated and in use.

        if not selected.allocated:
            return HttpResponseForbidden("Session is not currently in use")

        # Check that are owner of session, or a staff member.

        if not request.user.is_staff:
            if selected.owner != request.user:
                return HttpResponseForbidden("Access to session not permitted")

        return JsonResponse({"owner": selected.owner.username})

session_authorize = SessionAuthorizationEndpoint.as_view()
