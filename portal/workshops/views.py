from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

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
                available=True).count()
        details['available'] = available

        sessions = Session.objects.filter(environment=environment,
                available=False, owner=request.user)
        details['session'] = sessions and sessions[0] or None

        catalog.append(details)

    context = {"catalog": catalog}

    return render(request, 'workshops/catalog.html', context)

@login_required
def session(request, environment):
    context = {}

    return render(request, 'workshops/session.html', context)
