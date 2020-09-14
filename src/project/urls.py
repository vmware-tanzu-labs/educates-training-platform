from django.contrib import admin
from django.urls import include, path

from . import views

import oauth2_provider.views as oauth2_views

oauth2_endpoint_views = [
    path("authorize/", oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path("token/", oauth2_views.TokenView.as_view(), name="token"),
    path("revoke-token/", oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/create/", views.accounts_create, name="accounts_create"),
    path("accounts/", include("django_registration.backends.one_step.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("workshops/", include("project.apps.workshops.urls")),
    path("oauth2/", include(oauth2_endpoint_views)),
    path("", views.index, name="index"),
]
