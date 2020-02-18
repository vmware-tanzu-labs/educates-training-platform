import os

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django import forms

PORTAL_PASSWORD = os.environ.get('PORTAL_PASSWORD', 'eduk8s')

def index(request):
    if not request.session.get('email'):
        return HttpResponseRedirect(reverse('register'))
    return HttpResponseRedirect(reverse('session'))

class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data['password']
        if password != PORTAL_PASSWORD:
            raise forms.ValidationError('Incorrect access code!')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            request.session['email'] = form.cleaned_data['email']
            return HttpResponseRedirect(reverse('session'))
        else:
            return render(request, 'eduk8s/register.html', {'form': form})

    else:
        form = RegistrationForm()

    return render(request, 'eduk8s/register.html', {'form': form})

def session(request):
    return render(request, 'eduk8s/session.html')
