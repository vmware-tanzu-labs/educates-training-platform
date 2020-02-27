from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, JsonResponse

from oauth2_provider.views.generic import ProtectedResourceView

from .models import Environment, Session

@login_required
def catalog(request):
    catalog = []

    for environment in Environment.objects.all().order_by('name'):
        details = {}
        details['environment'] = environment.name
        details['workshop'] = environment.workshop

        available = Session.objects.filter(environment=environment,
                reserved=False, state="running").count()
        details['available'] = available

        sessions = environment.session_set.filter(reserved=True, state="running", owner=request.user)
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

    # Determine if there is already a reserved session which the current
    # user is an owner of.

    session = None

    sessions = selected.session_set.filter(reserved=True, state="running", owner=request.user)

    if not sessions:
        # Allocate a session by getting all the sessions which have not
        # been reserved and reserve one.

        sessions = selected.session_set.filter(reserved=False, state="running")

        if sessions:
            session = sessions[0]

            session.owner = request.user
            session.reserved = True

            session.save()

    else:
        session = sessions[0]

    if session:
        return redirect(f'http://{session.hostname}/')

    context['session'] = session

    return render(request, 'workshops/environment.html', context)

class SessionAuthorizationEndpoint(ProtectedResourceView):
    def get(self, request, session):
        # Ensure that the session exists.

        try:
             selected = Session.objects.get(name=session)
        except Session.DoesNotExist:
            raise Http404("Session does not exist")

        # Check that session is reserved and in use.

        if not selected.reserved:
            return HttpResponseForbidden("Session is not currently in use")

        # Check that are owner of session, or a staff member.

        if not request.user.is_staff:
            if selected.owner != request.user:
                return HttpResponseForbidden("Access to session not permitted")

        return JsonResponse({"owner": selected.owner.username})

session_authorize = SessionAuthorizationEndpoint.as_view()
