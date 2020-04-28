import json

from django.db import models
from django.contrib.auth.models import User

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
    name = models.CharField(max_length=255, primary_key=True)
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
    name = models.CharField(max_length=256, primary_key=True)
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT)
    capacity = models.IntegerField(default=0)
    initial = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    inactivity = models.IntegerField(default=0)
    tally = models.IntegerField(default=0)
    resource = JSONField(default={})

class Session(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    id = models.CharField(max_length=64)
    application = models.ForeignKey(Application, blank=True, null=True, on_delete=models.PROTECT)
    state = models.CharField(max_length=16, default="starting")
    allocated = models.BooleanField(default=False)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    created = models.DateTimeField(null=True, blank=True)
    started = models.DateTimeField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    anonymous = models.BooleanField(default=False)
    token = models.CharField(max_length=256, null=True, blank=True)
    redirect = models.URLField(null=True, blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)
