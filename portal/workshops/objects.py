import os

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.incluster_config
import kubernetes.config.config_exception
import kubernetes.client.rest

from .models import (
    Workshop, 
    Session, 
    Environment, 
)

from wrapt import synchronized

try:
    kubernetes.config.incluster_config.load_incluster_config()
except kubernetes.config.config_exception.ConfigException:
    kubernetes.config.load_kube_config()

custom_objects_api = kubernetes.client.CustomObjectsApi()

@synchronized
def refresh(name=None):
    name = os.environ.get('TRAINING_PORTAL', name)

    if not name:
        return False

    if Environment.objects.all().count():
        return True

    try:
        training_portal_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "trainingportals", name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            return False
        raise

    status = training_portal_instance.get("status", {}).get("eduk8s", {})

    if not status:
        return False

    workshops = status.get("workshops", [])
    environments = status.get("environments", [])

    if not environments:
        return True

    for workshop in workshops:
        Workshop.objects.get_or_create(**workshop)

    for environment in environments:
        workshop_instance = Workshop.objects.get(
                name=environment["workshop"]["name"])

        environment_instance, _ = Environment.objects.get_or_create(
                name=environment["name"], workshop=workshop_instance)

        for session in environment["sessions"]:
            session_instance, created = Session.objects.get_or_create(**session)
            if created:
                environment_instance.sessions.add(session_instance)
