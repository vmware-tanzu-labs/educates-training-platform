from django.db import models
from django.contrib.auth.models import User

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
    tally = models.IntegerField(default=0)

class Session(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    id = models.CharField(max_length=64)
    hostname = models.CharField(max_length=256)
    secret = models.CharField(max_length=128)
    state = models.CharField(max_length=16, default="starting")
    reserved = models.BooleanField(default=True)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)
