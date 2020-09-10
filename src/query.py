import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.incluster_config
import kubernetes.config.config_exception

try:
    kubernetes.config.incluster_config.load_incluster_config()
except kubernetes.config.config_exception.ConfigException:
    kubernetes.config.load_kube_config()

custom_objects_api = kubernetes.client.CustomObjectsApi()

training_portal_instance = custom_objects_api.get_cluster_custom_object(
    "training.eduk8s.io", "v1alpha1", "trainingportals", "xxx"
)

status = training_portal_instance.get("status", {})
workshops = status.get("eduk8s", {}).get("workshops", [])
environments = status.get("eduk8s", {}).get("environments", [])

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduk8s.settings")

import django
django.setup()

from django.core.exceptions import ObjectDoesNotExist

from workshops.models import (
    Workshop, 
    Session, 
    Environment, 
)

for workshop in workshops:
    try:
        workshop_instance = Workshop.objects.get(name=workshop["name"])
    except ObjectDoesNotExist:
        workshop_instance = Workshop.objects.create(**workshop)

for environment in environments:
    try:
        environment_instance = Environment.objects.get(name=environment["name"])
    except ObjectDoesNotExist:
        environment_instance = Environment.objects.create(name=environment["name"],
            workshop=workshop_instance)

    for session in environment["sessions"]:
        try:
            session_instance = Session.objects.get(name=session["name"])
        except ObjectDoesNotExist:
            session_instance = Session.objects.create(**session)
            environment_instance.sessions.add(session_instance)
