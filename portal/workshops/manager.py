import os
import time
import string
import random
import traceback

from datetime import timedelta

import requests

from threading import Thread, Lock
from queue import Queue, Empty

import wrapt

import kubernetes
import kubernetes.client

from django.db import transaction

from workshops.models import Workshop, SessionState, Session, Environment

from django.contrib.auth.models import User, Group
from django.utils import timezone

from oauth2_provider.models import Application

portal_name = os.environ.get("TRAINING_PORTAL", "")

ingress_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
ingress_secret = os.environ.get("INGRESS_SECRET", "")
ingress_protocol = os.environ.get("INGRESS_PROTOCOL", "http")

portal_hostname = os.environ.get("PORTAL_HOSTNAME", f"{portal_name}-ui.{ingress_domain}")

admin_username = os.environ.get("ADMIN_USERNAME", "eduk8s")

worker_queue = Queue()

class Action:

    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        worker_queue.put(dict(action=self.name, args=args, kwargs=kwargs))

class Scheduler:

    def __init__(self):
        self._lock = Lock()

    def __getattr__(self, name):
        return Action(name)

    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args, **kwargs):
        return self._lock.__exit__(*args, **kwargs)

scheduler = Scheduler()

def worker():
    while True:
        try:
            item = worker_queue.get(timeout=15)
        except Empty:
            scheduler.purge_expired_workshop_sessions()
            continue

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

def convert_duration_to_seconds(size):
    multipliers = {
        's': 1,
        'm': 60,
        'h': 60*60,
    }

    size = str(size)

    for suffix in multipliers:
        if size.lower().endswith(suffix):
            return int(size[0:-len(suffix)]) * multipliers[suffix]
    else:
        if size.lower().endswith('b'):
            return int(size[0:-1])

    try:
        return int(size)
    except ValueError:
        raise RuntimeError('"%s" is not a time duration. Must be an integer or a string with suffix s, m or h.' % size)

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

    if status is None or not status.get("url"):
        scheduler.delay_execution(delay=5)
        scheduler.process_training_portal()
        print(f"WARNING: Training portal {portal_name} is not ready.")
        return

    # Ensure that external access setup for robot user account.

    robot_username = status["credentials"]["robot"]["username"]
    robot_password = status["credentials"]["robot"]["password"]

    robot_client_id = status["clients"]["robot"]["id"]
    robot_client_secret = status["clients"]["robot"]["secret"]

    try:
        user = User.objects.get(username=robot_username)
    except User.DoesNotExist:
        user = User.objects.create_user(robot_username, password=robot_password)

    group, _ = Group.objects.get_or_create(name="robots")

    user.groups.add(group)

    user.save()

    application, _ = Application.objects.get_or_create(
            name="robot@eduk8s",
            client_id=robot_client_id,
            user=user,
            client_type="public",
            authorization_grant_type="password",
            client_secret=robot_client_secret)

    # Ensure that database entries exist for each workshop used.

    workshops = status.get("workshops", [])

    for workshop in workshops:
        Workshop.objects.get_or_create(**workshop)

    # Get the list of workshop environments from the status and schedule
    # processing of each one.

    environments = status.get("environments", [])

    default_capacity = training_portal["spec"].get("portal", {}).get("capacity", 0)
    default_reserved = training_portal["spec"].get("portal", {}).get("reserved", default_capacity)
    default_initial = training_portal["spec"].get("portal", {}).get("initial", default_reserved)
    default_expires = training_portal["spec"].get("portal", {}).get("expires", "0m")
    default_orphaned = training_portal["spec"].get("portal", {}).get("orphaned", "0m")

    for environment in environments:
        workshop = Workshop.objects.get(name=environment["workshop"]["name"])

        if environment.get("capacity") is not None:
            workshop_capacity = environment.get("capacity", default_capacity)
            workshop_reserved = environment.get("reserved", workshop_capacity)
            workshop_initial = environment.get("initial", workshop_reserved)
        else:
            workshop_capacity = default_capacity
            workshop_reserved = default_reserved
            workshop_initial = default_initial

        workshop_capacity = max(0, workshop_capacity)
        workshop_reserved = max(0, min(workshop_reserved, workshop_capacity))
        workshop_initial = max(0, min(workshop_initial, workshop_capacity))

        if workshop_initial < workshop_reserved:
            workshop_initial = workshop_reserved

        workshop_expires = environment.get("expires", default_expires)
        workshop_orphaned = environment.get("orphaned", default_orphaned)

        duration = timedelta(seconds=max(0,
                convert_duration_to_seconds(workshop_expires)))
        inactivity = timedelta(seconds=max(0,
                convert_duration_to_seconds(workshop_orphaned)))

        scheduler.process_workshop_environment(
            name=environment["name"], workshop=workshop,
            capacity=workshop_capacity, initial=workshop_initial,
            reserved=workshop_reserved, duration=duration, inactivity=inactivity)

def initiate_workshop_session(workshop_environment, **session_kwargs):
    environment_status = workshop_environment.resource["status"]["eduk8s"]
    workshop_spec = environment_status["workshop"]["spec"]

    tally = workshop_environment.tally = workshop_environment.tally+1

    workshop_environment.save()

    session_id = f"s{tally:03}"
    session_name = f"{workshop_environment.name}-{session_id}"
    session_hostname = f"{session_name}.{ingress_domain}"

    characters = string.ascii_letters + string.digits
    secret = "".join(random.sample(characters, 32))

    redirect_uris = [f"{ingress_protocol}://{session_hostname}/oauth_callback"]

    redirect_uris.append(f"{ingress_protocol}://{session_name}-console.{ingress_domain}/oauth_callback")
    redirect_uris.append(f"{ingress_protocol}://{session_name}-editor.{ingress_domain}/oauth_callback")
    redirect_uris.append(f"{ingress_protocol}://{session_name}-slides.{ingress_domain}/oauth_callback")
    redirect_uris.append(f"{ingress_protocol}://{session_name}-terminal.{ingress_domain}/oauth_callback")

    ingresses = workshop_spec.get("session", {}).get("ingresses", [])

    for ingress in ingresses:
        session_ingress_hostname = f"{session_name}-{ingress['name']}.{ingress_domain}"
        redirect_uris.append(f"{ingress_protocol}://{session_ingress_hostname}/oauth_callback")

    eduk8s_user = User.objects.get(username=admin_username)

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
            application=application,
            created=session_kwargs.get("started", timezone.now()),
            environment=workshop_environment,
            **session_kwargs)

    return session

@wrapt.synchronized(scheduler)
@transaction.atomic
def process_workshop_environment(name, workshop, capacity, initial, reserved, duration, inactivity):
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
            name=name, workshop=workshop, capacity=capacity, initial=initial,
            reserved=reserved, duration=duration, inactivity=inactivity)
        print(f"WARNING: Workshop environment {name} is not ready.")
        return

    # See if we already have a entry in the database for the workshop
    # environment, meaning we have already processed it, and do not need
    # to try again. Otherwise a database entry gets created.

    workshop_environment, created = Environment.objects.get_or_create(
        name=name, workshop=workshop, capacity=capacity, initial=initial,
        reserved=reserved, duration=duration, inactivity=inactivity,
        resource=workshop_environment_k8s)

    if not created:
        return

    # Since this is first time we have seen the workshop environment,
    # we need to trigger the creation of the workshop sessions.

    sessions = []

    for _ in range(initial):
        sessions.append(initiate_workshop_session(workshop_environment))

    def _schedule_session_creation():
        for session in sessions:
            scheduler.create_workshop_session(name=session.name)

    transaction.on_commit(_schedule_session_creation)

@transaction.atomic
def create_workshop_session(name):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # Lookup the workshop session that we need to create and make
    # sure it is still in starting state.

    session = Session.objects.get(name=name)

    if session.state != SessionState.STARTING:
        return

    # Create the WorkshopSession custom resource to trigger creation
    # of the actual workshop session.

    workshop_environment = session.environment

    environment_metadata = workshop_environment.resource["metadata"]
    environment_spec = workshop_environment.resource["spec"]

    session_env = list(environment_spec.get("session", {}).get("env"))
    session_env.append({"name": "PORTAL_CLIENT_ID", "value": session.name})
    session_env.append({"name": "PORTAL_CLIENT_SECRET", "value":
        session.application.client_secret})
    session_env.append(
        {"name": "PORTAL_API_URL", "value": f"{ingress_protocol}://{portal_hostname}"}
    )
    session_env.append({"name": "SESSION_NAME", "value": session.name})

    if workshop_environment.duration or workshop_environment.inactivity:
        restart_url = f"{ingress_protocol}://{portal_hostname}/workshops/session/{session.name}/delete/"
    else:
        restart_url = f"{ingress_protocol}://{portal_hostname}/workshops/catalog/"

    if workshop_environment.duration:
        session_env.append({"name": "ENABLE_COUNTDOWN", "value": "true"})

    session_env.append({"name": "RESTART_URL", "value": restart_url})

    session_body = {
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "kind": "WorkshopSession",
        "metadata": {
            "name": session.name,
            "labels": {
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": session.environment.name,
            },
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
                "ingress": {
                    "domain": ingress_domain,
                    "secret": ingress_secret,
                },
                "env": session_env,
            },
        },
    }

    custom_objects_api.create_cluster_custom_object(
       "training.eduk8s.io", "v1alpha1", "workshopsessions", session_body,
    )

    if session.owner:
        if session.token:
            session.state = SessionState.WAITING
        else:
            session.state = SessionState.RUNNING
    else:
        session.state = SessionState.WAITING

    # Make sure we save the update state of the session.

    session.save()

@wrapt.synchronized(scheduler)
def purge_expired_workshop_sessions():
    now = timezone.now()

    for session in Session.objects.all():
        if session.is_allocated():
            if session.expires and session.expires <= now:
                print(f"Session {session.name} expired. Deleting session.")
                scheduler.delete_workshop_session(session)
            elif session.environment.inactivity:
                try:
                    url = f"{ingress_protocol}://{session.name}.{ingress_domain}/session/activity"
                    r = requests.get(url)
                    if r.status_code == 200:
                        if r.json()["idle-time"] >= session.environment.inactivity:
                            print(f"Session {session.name} orphaned. Deleting session.")
                            scheduler.delete_workshop_session(session)
                except Exception:
                    pass

@wrapt.synchronized(scheduler)
@transaction.atomic
def delete_workshop_session(session):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    try:
        custom_objects_api.delete_cluster_custom_object(
           "training.eduk8s.io", "v1alpha1", "workshopsessions", session.name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            pass
        raise

    environment = session.environment

    if (environment.active_sessions_count()-1 < environment.capacity and
            environment.available_sessions_count() < environment.reserved):
        replacement_session = initiate_workshop_session(environment)
        transaction.on_commit(lambda: scheduler.create_workshop_session(
                name=replacement_session.name))

    session.mark_as_stopped()
