from django.contrib import admin

from .models import Workshop, Session, Environment

class WorkshopAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

class EnvironmentAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'workshop', 'initial', 'tally', 'resource')

class SessionAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(Workshop, WorkshopAdmin)
admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Session, SessionAdmin)
