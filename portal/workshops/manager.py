import os
import time
import string
import random
import traceback

from threading import Thread
from queue import Queue

import kubernetes
import kubernetes.client

from django.db import transaction

from workshops.models import Workshop, Session, Environment

from django.contrib.auth.models import User

from oauth2_provider.models import Application

portal_name = os.environ.get("TRAINING_PORTAL", "")
ingress_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")

worker_queue = Queue()

class Action:

    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        worker_queue.put(dict(action=self.name, args=args, kwargs=kwargs))

class Scheduler:

    def __getattr__(self, name):
        return Action(name)

scheduler = Scheduler()

def worker():
    while True:
        item = worker_queue.get()
        if item is None:
            break
        try:
            action = item["action"]
            function = globals()[action]

            args = item.get("args", {})
            kwargs = item.get("kwargs", {})

            print(f"INFO: Executing {action}, args={args}, kwargs={kwargs}")

            function(*args, **kwargs)

        except Exception as e:
            traceback.print_exc()

        worker_queue.task_done()

manager_thread = Thread(target=worker)

def initialize():
    try:
        kubernetes.config.incluster_config.load_incluster_config()
    except kubernetes.config.config_exception.ConfigException:
        kubernetes.config.load_kube_config()

    manager_thread.start()

    scheduler.process_training_portal()

def delay_execution(delay):
    # Force a delay in processing of actions. Only use this during the
    # initial startup to trigger retry waiting for training portal.

    time.sleep(delay)

def process_training_portal():
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # If we already have workshop environment entries in the database
    # then we don't need to do anything.

    if Environment.objects.all().count():
        return

    # Lookup the training portal custom resource for this instance.
    # If it doesn't exist, then sleep for a while and try again.

    try:
        training_portal = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "trainingportals", portal_name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            scheduler.delay_execution(delay=5)
            scheduler.process_training_portal()
            print(f"WARNING: Training portal {portal_name} does not exist.")
            return
        raise

    # Ensure that the status has been updated for the training portal
    # with the list of workshop environments.

    status = training_portal.get("status", {}).get("eduk8s")

    if status is None:
        scheduler.delay_execution(delay=5)
        scheduler.process_training_portal()
        print(f"WARNING: Training portal {portal_name} is not ready.")
        return

    # Ensure that database entries exist for each workshop used.

    workshops = status.get("workshops", [])

    for workshop in workshops:
        Workshop.objects.get_or_create(**workshop)

    # Get the list of workshop environments from the status and schedule
    # processing of each one.

    environments = status.get("environments", [])

    default_capacity = training_portal["spec"].get("portal", {}).get("capacity", 0)
    default_reserved = training_portal["spec"].get("portal", {}).get("reserved", default_capacity)

    for environment in environments:
        workshop = Workshop.objects.get(name=environment["workshop"]["name"])

        if environment["workshop"].get("capacity") is not None:
            workshop_capacity = environment["workshop"].get("capacity", default_capacity)
            workshop_reserved = environment["workshop"].get("reserved", workshop_capacity)
        else:
            workshop_capacity = default_capacity
            workshop_reserved = default_reserved

        workshop_capacity = max(0, workshop_capacity)
        workshop_reserved = max(0, min(workshop_reserved, workshop_capacity))

        scheduler.process_workshop_environment(
            name=environment["name"], workshop=workshop,
            capacity=workshop_capacity, reserved=workshop_reserved)

def initiate_workshop_session(workshop_environment):
    environment_status = workshop_environment.resource["status"]["eduk8s"]
    workshop_spec = environment_status["workshop"]["spec"]

    tally = workshop_environment.tally = workshop_environment.tally+1

    workshop_environment.save()

    domain = workshop_environment.resource["spec"].get("session", {}).get(
            "domain", ingress_domain)

    session_id = f"s{tally:03}"
    session_name = f"{workshop_environment.name}-{session_id}"
    session_hostname = f"{session_name}.{domain}"

    characters = string.ascii_letters + string.digits
    secret = "".join(random.sample(characters, 32))

    redirect_uris = [f"http://{session_hostname}/oauth_callback"]

    for session_ingress_name in ["terminal", "console", "editor", "slides"]:
        session_ingress_hostname = f"{session_name}-{session_ingress_name}.{domain}"
        redirect_uris.append(f"http://{session_ingress_hostname}/oauth_callback")

    ingresses = workshop_spec.get("session", {}).get("ingresses", [])

    for ingress in ingresses:
        session_ingress_hostname = f"{session_name}-{ingress['name']}.{domain}"
        redirect_uris.append(f"http://{session_ingress_hostname}/oauth_callback")

    eduk8s_user = User.objects.get(username="eduk8s")

    application, _ = Application.objects.get_or_create(
            name=session_name,
            client_id=session_name,
            user=eduk8s_user,
            redirect_uris=" ".join(redirect_uris),
            client_type="public",
            authorization_grant_type="authorization-code",
            client_secret=secret,
            skip_authorization=True)

    session = Session.objects.create(
            name=session_name,
            id=session_id,
            domain=domain,
            secret=secret,
            environment=workshop_environment)

    return session

@transaction.atomic
def process_workshop_environment(name, workshop, capacity, reserved):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # Ensure that the workshop environment exists and is ready.

    try:
        workshop_environment_k8s = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopenvironments", name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            print(f"ERROR: Workshop environment {name} does not exist.")
            return

        raise

    status = workshop_environment_k8s.get("status", {}).get("eduk8s")

    if status is None:
        scheduler.delay_execution(delay=5)
        scheduler.process_training_portal()
        scheduler.process_workshop_environment(
            name=name, workshop=workshop, capacity=capacity, reserved=reserved)
        print(f"WARNING: Workshop environment {name} is not ready.")
        return

    # See if we already have a entry in the database for the workshop
    # environment, meaning we have already processed it, and do not need
    # to try again. Otherwise a database entry gets created.

    workshop_environment, created = Environment.objects.get_or_create(
        name=name, workshop=workshop, capacity=capacity, reserved=reserved,
        resource=workshop_environment_k8s)

    if not created:
        return

    # Since this is first time we have seen the workshop environment,
    # we need to trigger the creation of the workshop sessions.

    sessions = []

    for _ in range(reserved):
        sessions.append(initiate_workshop_session(workshop_environment))

    def _schedule_session_creation():
        for session in sessions:
            scheduler.create_workshop_session(name=session.name)

    transaction.on_commit(_schedule_session_creation)

@transaction.atomic
def create_workshop_session(name):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # Lookup the workshop session that we need to created and make
    # sure it is still in starting state.

    session = Session.objects.get(name=name)

    if session.state != "starting":
        return

    # Create the WorkshopSession custom resource to trigger creation
    # of the actual workshop session.

    workshop_environment = session.environment

    environment_metadata = workshop_environment.resource["metadata"]
    environment_spec = workshop_environment.resource["spec"]

    domain = environment_spec.get("session", {}).get("domain", ingress_domain)

    portal_hostname = f"{portal_name}-ui.{domain}"

    session_env = list(environment_spec.get("session", {}).get("env"))
    session_env.append({"name": "PORTAL_CLIENT_ID", "value": session.name})
    session_env.append({"name": "PORTAL_CLIENT_SECRET", "value": session.secret})
    session_env.append(
        {"name": "PORTAL_API_URL", "value": f"http://{portal_hostname}"}
    )
    session_env.append({"name": "SESSION_NAME", "value": session.name})

    session_env.append({"name": "RESTART_URL", "value": f"http://{portal_hostname}"})

    session_body = {
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "kind": "WorkshopSession",
        "metadata": {
            "name": session.name,
            "labels": {"workshop-environment": session.environment.name,},
            "ownerReferences": [
                {
                    "apiVersion": "v1alpha1",
                    "kind": "WorkshopEnvironment",
                    "blockOwnerDeletion": False,
                    "controller": True,
                    "name": session.environment.name,
                    "uid": environment_metadata["uid"],
                }
            ]
        },
        "spec": {
            "environment": {"name": session.environment.name},
            "session": {
                "id": session.id,
                "username": "",
                "password": "",
                "domain": session.domain,
                "env": session_env,
            },
        },
    }

    custom_objects_api.create_cluster_custom_object(
       "training.eduk8s.io", "v1alpha1", "workshopsessions", session_body,
    )

    session.state = "running"
    session.allocated = False

    # Make sure we save the update state of the session.

    session.save()
