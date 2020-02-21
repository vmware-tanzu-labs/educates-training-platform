from django.shortcuts import render, redirect

def index(request):
    if not request.user.is_authenticated:
        return redirect('django_registration_register')
    return redirect('workshops_catalog')
