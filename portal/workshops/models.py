import json
import enum

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from oauth2_provider.models import Application

class JSONField(models.Field):
    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return self.to_python(value)
        return value

    def to_python(self, value):
        if value is not None:
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return value
        return value

    def get_prep_value(self, value):
        if value is not None:
            return str(json.dumps(value))
        return value

    def value_to_string(self, obj):
        return self.value_from_object(obj)

class Workshop(models.Model):
    name = models.CharField(verbose_name="workshop name", max_length=255,
            primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    vendor = models.CharField(max_length=128)
    authors = JSONField(default=[])
    difficulty = models.CharField(max_length=128)
    duration = models.CharField(max_length=128)
    tags = JSONField(default=[])
    logo = models.TextField()
    url = models.CharField(max_length=255)
    content = JSONField(default={})

class Environment(models.Model):
    name = models.CharField(verbose_name="environment name", max_length=256,
            primary_key=True)
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT)
    capacity = models.IntegerField(verbose_name="maximum capacity", default=0)
    initial = models.IntegerField(verbose_name="initial instances", default=0)
    reserved = models.IntegerField(verbose_name="reserved instances", default=0)
    duration = models.DurationField(verbose_name="workshop duration", default=0)
    inactivity = models.DurationField(verbose_name="inactivity timeout", default=0)
    tally = models.IntegerField(verbose_name="workshop tally", default=0)
    resource = JSONField(verbose_name="resource definition", default={})

    def workshop_name(self):
        return self.workshop.name

    workshop_name.admin_order_field = "workshop__name"

    def available_sessions(self):
        return self.session_set.filter(owner__isnull=True,
                state__in=(SessionState.STARTING, SessionState.WAITING))

    def available_sessions_count(self):
        return self.available_sessions().count()

    available_sessions_count.short_description = "Available"

    def allocated_sessions(self):
        return self.session_set.filter(state__in=(
                SessionState.STARTING, SessionState.WAITING,
                SessionState.RUNNING, SessionState.STOPPING)).exclude(
                owner__isnull=True)

    def allocated_sessions_count(self):
        return self.allocated_sessions().count()

    allocated_sessions_count.short_description = "Allocated"

    def allocated_session_for_user(self, user):
        sessions = self.session_set.filter(state__in=(SessionState.STARTING,
                SessionState.WAITING, SessionState.RUNNING,
                SessionState.STOPPING), owner=user)
        if sessions:
            return sessions[0]

    def active_sessions(self):
        return self.session_set.filter(state__in=(
                SessionState.STARTING, SessionState.WAITING,
                SessionState.RUNNING, SessionState.STOPPING))

    def active_sessions_count(self):
        return self.active_sessions().count()

    active_sessions_count.short_description = "Active"

class SessionState(enum.IntEnum):
    STARTING = 1
    WAITING = 2
    RUNNING = 3
    STOPPING = 4
    STOPPED = 5

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

class Session(models.Model):
    name = models.CharField(verbose_name="session name", max_length=256,
            primary_key=True)
    id = models.CharField(max_length=64)
    application = models.ForeignKey(Application, blank=True,
            null=True, on_delete=models.PROTECT)
    state = models.IntegerField(choices=SessionState.choices(),
            default=SessionState.STARTING)
    owner = models.ForeignKey(User, blank=True, null=True,
            on_delete=models.PROTECT)
    created = models.DateTimeField(null=True, blank=True)
    started = models.DateTimeField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    token = models.CharField(max_length=256, null=True, blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)

    def environment_name(self):
        return self.environment.name

    environment_name.admin_order_field = "environment__name"

    def workshop_name(self):
        return self.environment.workshop.name

    workshop_name.admin_order_field = "environment__workshop__name"

    def is_available(self):
        return self.owner is None and self.state in (SessionState.STARTING,
                SessionState.WAITING)

    is_available.short_description = "Available"
    is_available.boolean = True

    def is_allocated(self):
        return self.owner is not None and self.state != SessionState.STOPPED

    is_allocated.short_description = "Allocated"
    is_allocated.boolean = True

    def is_stopped(self):
        return self.state == SessionState.STOPPED

    is_stopped.short_description = "Stopped"
    is_stopped.boolean = True

    def remaining_time(self):
        now = timezone.now()
        if self.is_allocated() and self.expires:
            if now >= self.expires:
                return 0

            return (self.expires - now).total_seconds()

    def remaining_time_as_string(self):
        remaining = self.remaining_time()
        if remaining is not None:
            return "%02d:%02d" % (remaining/60, remaining%60)

    remaining_time_as_string.short_description = "Remaining"

    def mark_as_stopped(self):
        application = self.application
        self.state = SessionState.STOPPED
        self.expires = timezone.now()
        self.application = None
        self.save()
        application.delete()

    @staticmethod
    def allocated_session(name, user=None):
        try:
            session = Session.objects.get(name=name, state__in=(
                        SessionState.STARTING, SessionState.WAITING,
                        SessionState.RUNNING, SessionState.STOPPING))
            if user:
                if session.owner == user:
                    return session
            else:
                return session
        except Session.DoesNotExist:
            pass
