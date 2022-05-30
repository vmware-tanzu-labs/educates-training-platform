from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import (
    TrainingPortal,
    Workshop,
    Session,
    SessionState,
    Environment,
    EnvironmentState,
)


class TrainingPortalAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "uid",
        "generation",
        "overall_capacity",
        "available_sessions_count",
        "allocated_sessions_count",
        "update_workshop",
    ]

    fields = [
        "name",
        "uid",
        "generation",
        "sessions_maximum",
        "sessions_registered",
        "sessions_anonymous",
        "default_capacity",
        "default_reserved",
        "default_initial",
        "default_expires",
        "default_overtime",
        "default_deadline",
        "default_orphaned",
        "update_workshop",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class WorkshopAdmin(admin.ModelAdmin):
    list_display = ["name", "uid", "generation"]

    exclude = ["logo"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "uid",
        "workshop_name",
        "expires",
        "state",
        "capacity",
        "available_sessions_count",
        "allocated_sessions_count",
    ]

    fields = [
        "workshop_link",
        "name",
        "uid",
        "position",
        "expires",
        "overtime",
        "deadline",
        "orphaned",
        "capacity",
        "state",
        "reserved",
        "initial",
        "env",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    actions = [
        "recyle_environments",
    ]

    def recyle_environments(self, request, queryset):
        for environment in queryset:
            if environment.state not in (EnvironmentState.STOPPING, EnvironmentState.STOPPED):
                # XXX Need to do a delayed import else when collecting static
                # files when building container images it attempts to contact
                # Kubernetes REST API. Have to work out how can refactor the
                # code to avoid that occuring. Hope we don't end up with a
                # thread deadlocking issue due to this.
                from .manager.environments import replace_workshop_environment
                replace_workshop_environment(environment)

    recyle_environments.short_description = "Recycle Environments"

class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "workshop_link",
        "environment_link",
        "is_available",
        "is_allocated",
        "is_stopping",
        "is_stopped",
        "remaining_time_as_string",
    ]

    list_filter = ["environment__name", "environment__workshop_name"]

    fields = [
        "name",
        "workshop_link",
        "environment_link",
        "state",
        "owner",
        "created",
        "started",
        "expires",
        "url_link",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    actions = [
        "expire_sessions",
        "extend_sessions_10m",
        "extend_sessions_30m",
        "extend_sessions_60m",
        "purge_sessions",
    ]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def expire_sessions(self, request, queryset):
        for session in queryset:
            if session.is_allocated():
                if session.state != SessionState.STOPPING:
                    session.state = SessionState.STOPPING
                    session.expires = session.deadline = timezone.now() + timedelta(minutes=1)
                    session.save()
            elif session.is_available():
                session.state = SessionState.STOPPING
                session.expires = session.deadline = timezone.now()
                session.save()

    expire_sessions.short_description = "Expire Sessions"

    def extend_sessions(self, request, queryset, minutes):
        for session in queryset:
            if session.is_allocated() and session.expires:
                if session.state == SessionState.STOPPING:
                    session.state = SessionState.RUNNING
                session.expires += timedelta(minutes=minutes)
                if session.expires > session.started + session.environment.deadline:
                    session.expires = session.started + session.environment.deadline
                session.save()

    def extend_sessions_10m(self, request, queryset):
        self.extend_sessions(request, queryset, 10)

    extend_sessions_10m.short_description = "Extend Sessions (10m)"

    def extend_sessions_30m(self, request, queryset):
        self.extend_sessions(request, queryset, 30)

    extend_sessions_30m.short_description = "Extend Sessions (30m)"

    def extend_sessions_60m(self, request, queryset):
        self.extend_sessions(request, queryset, 60)

    extend_sessions_60m.short_description = "Extend Sessions (60m)"

    def purge_sessions(self, request, queryset):
        for session in queryset:
            if session.is_stopped():
                session.delete()

    purge_sessions.short_description = "Purge Sessions"


admin.site.register(TrainingPortal, TrainingPortalAdmin)
admin.site.register(Workshop, WorkshopAdmin)
admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Session, SessionAdmin)
