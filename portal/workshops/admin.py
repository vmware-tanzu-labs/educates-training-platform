from django.contrib import admin

from .models import Workshop, Session, Environment

admin.site.register(Workshop)
admin.site.register(Session)
admin.site.register(Environment)
