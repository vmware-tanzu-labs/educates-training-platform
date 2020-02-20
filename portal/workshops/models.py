from django.db import models

class Workshop(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    vendor = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    description = models.TextField(max_length=1024)
    url = models.CharField(max_length=512)

class Session(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    id = models.CharField(max_length=64)
    hostname = models.CharField(max_length=256)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=128)

class Environment(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT)
    sessions = models.ManyToManyField(Session)
