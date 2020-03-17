import json

from django.db import models
from django.contrib.auth.models import User

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
    name = models.CharField(max_length=256, primary_key=True)
    vendor = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    description = models.TextField(max_length=1024)
    url = models.CharField(max_length=512)

class Environment(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT)
    capacity = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    tally = models.IntegerField(default=0)
    resource = JSONField(default={})

class Session(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    id = models.CharField(max_length=64)
    domain = models.CharField(max_length=256)
    secret = models.CharField(max_length=128)
    state = models.CharField(max_length=16, default="starting")
    allocated = models.BooleanField(default=True)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    expires = models.DateTimeField(null=True, blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)
