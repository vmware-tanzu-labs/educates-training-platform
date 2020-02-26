import os

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.incluster_config
import kubernetes.config.config_exception
import kubernetes.client.rest

from django.contrib.auth.models import User

from .models import (
    Workshop,
    Session,
    Environment,
    Application
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

        eduk8s_user = User.objects.get(username="eduk8s")

        for session in environment["sessions"]:
            application_instance = Application.objects.get_or_create(
                    name=session["name"],
                    client_id=session["name"], user=eduk8s_user,
                    redirect_uris="http://"+session["hostname"]+"/oauth_callback",
                    client_type="public",
                    authorization_grant_type="authorization-code",
                    client_secret=session["secret"],
                    skip_authorization=True)

            session_instance, created = Session.objects.get_or_create(**session)

            if created:
                environment_instance.sessions.add(session_instance)
