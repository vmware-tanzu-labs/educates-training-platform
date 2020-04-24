from django.contrib import admin

from .models import Workshop, Session, Environment

class WorkshopAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'title', 'description', 'vendor', 'authors',
            'difficulty', 'duration', 'tags', 'logo', 'url', 'image', 'content')

class EnvironmentAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'workshop', 'capacity', 'reserved', 'tally', 'resource')

class SessionAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'id', 'application', 'state', 'environment')

admin.site.register(Workshop, WorkshopAdmin)
admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Session, SessionAdmin)
