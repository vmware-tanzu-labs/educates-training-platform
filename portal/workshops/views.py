from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from . import objects
from .models import Environment

@login_required
def catalog(request):
    objects.refresh()

    catalog = [{"environment": e.name, "workshop":e.workshop} for e in
            Environment.objects.all().order_by('name')]

    context = {"catalog": catalog}

    return render(request, 'workshops/catalog.html', context)

@login_required
def session(request, environment):
    context = {}

    return render(request, 'workshops/session.html', context)
