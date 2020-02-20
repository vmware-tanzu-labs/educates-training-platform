from django.contrib import admin

from .models import Workshop, Session, Environment

class WorkshopAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'vendor', 'title', 'description', 'url')

class SessionAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'id', 'hostname', 'username', 'password')

class EnvironmentAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'workshop', 'sessions')

admin.site.register(Workshop, WorkshopAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Environment, EnvironmentAdmin)
