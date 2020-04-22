from django.shortcuts import render, redirect
from django.conf import settings

def index(request):
    if not request.user.is_authenticated:
        if settings.REGISTRATION_OPEN:
            return redirect('django_registration_register')
        else:
            return redirect('login')

    return redirect('workshops_catalog')
