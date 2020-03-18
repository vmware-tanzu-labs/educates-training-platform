from django.urls import include, path

from . import views

urlpatterns = [
    path('catalog/', views.catalog, name='workshops_catalog'),
    path('environment/<slug:name>/', views.environment,
            name='workshops_environment'),
    path('session/<slug:session>/authorize/', views.session_authorize,
            name='workshops_session_authorize'),
]
