from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404

from . import objects
from .models import Environment, Session

@login_required
def catalog(request):
    objects.refresh()

    catalog = []

    for environment in Environment.objects.all().order_by('name'):
        details = {}
        details['environment'] = environment.name
        details['workshop'] = environment.workshop

        available = Session.objects.filter(environment=environment,
                reserved=False).count()
        details['available'] = available

        sessions = Session.objects.filter(environment=environment,
                reserved=True, owner=request.user)
        details['session'] = sessions and sessions[0] or None

        catalog.append(details)

    context = {"catalog": catalog}

    return render(request, 'workshops/catalog.html', context)

@login_required
@transaction.atomic
def session(request, environment):
    context = {}

    # Ensure there is an environment which the specified name in existance.

    try:
         selected = Environment.objects.get(name=environment)
    except Environment.DoesNotExist:
        raise Http404("Environment does not exist")

    # Determine if there is already a reserved session which the current
    # user is an owner of.

    session = None

    sessions = Session.objects.filter(environment=selected,
            reserved=True, owner=request.user)

    if not sessions:
        # Allocate a session by getting all the sessions which have not
        # been reserved and reserve one.

        sessions = Session.objects.filter(environment=selected,
                reserved=False)

        if sessions:
            session = sessions[0]

            session.owner = request.user
            session.reserved = True
            session.save()

    else:
        session = sessions[0]

    context['session'] = session

    return render(request, 'workshops/session.html', context)
