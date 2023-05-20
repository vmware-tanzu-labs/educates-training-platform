"""Defines view handlers for controlling access to workshops via the web
interface.

"""

__all__ = ["access"]

import os

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest
from django.conf import settings

from ..forms import AccessTokenForm


@require_http_methods(["GET", "POST"])
def access(request):
    """Renders login form when access to the training portal requires a simple
    access token be provided.

    """

    if request.method == "POST":
        form = AccessTokenForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            redirect_url = form.cleaned_data["redirect_url"]
            if settings.PORTAL_PASSWORD == password:
                request.session["is_allowed_access_to_event"] = True
                return redirect(redirect_url)
    else:
        redirect_url = request.GET.get("redirect_url")

        if not redirect_url:
            return HttpResponseBadRequest("Need redirect URL for access check")

        data = {"redirect_url": redirect_url}
        form = AccessTokenForm(initial=data)

    context = {"form": form}

    try:
        with open("/opt/app-root/static/theme/training-portal.html") as fp:
            context["portal_head_html"] = fp.read()
    except Exception:
        context["portal_head_html"] = ""

    return render(request, context)
