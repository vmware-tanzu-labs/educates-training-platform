from django.urls import include, path

from . import views

urlpatterns = [
    path('catalog/', views.catalog, name='workshops_catalog'),
    path('session/<slug:environment>/', views.session, name='workshops_session'),
]
