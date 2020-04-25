import os
import uuid

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.conf import settings

registration_type = os.environ.get('REGISTRATION_TYPE', 'one-step')
enable_registration = os.environ.get('ENABLE_REGISTRATION', 'true')

def accounts_create(request):
    if request.user.is_authenticated:
        return redirect('workshops_catalog')

    if enable_registration != 'true' or registration_type != 'anonymous':
        return redirect('login')

    created = False

    while not created:
        username = uuid.uuid4()
        user, created = User.objects.get_or_create(username=username)

    group, _ = Group.objects.get_or_create(name="anonymous")

    user.groups.add(group)

    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

    return redirect('workshops_catalog')

def index(request):
    if not request.user.is_authenticated:
        if registration_type == 'anonymous':
                return redirect('accounts_create')
        elif registration_type == 'one-step':
            if settings.REGISTRATION_OPEN:
                return redirect('django_registration_register')
            else:
                return redirect('login')
        else:
            return redirect('login')

    return redirect('workshops_catalog')
