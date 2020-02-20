from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
    if not request.user.is_authenticated:
        return redirect('django_registration_register')

    return render(request, 'eduk8s/index.html')

@login_required
def session(request):
    return render(request, 'eduk8s/session.html')
