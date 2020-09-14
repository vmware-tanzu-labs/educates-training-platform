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

from .models import TrainingPortal, Workshop, SessionState, Session, Environment

from django.contrib.auth.models import User, Group
from django.utils import timezone

from oauth2_provider.models import Application

portal_name = os.environ.get("TRAINING_PORTAL", "")

ingress_domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
ingress_secret = os.environ.get("INGRESS_SECRET", "")
ingress_protocol = os.environ.get("INGRESS_PROTOCOL", "http")

portal_hostname = os.environ.get("PORTAL_HOSTNAME", f"{portal_name}-ui.{ingress_domain}")

admin_username = os.environ.get("ADMIN_USERNAME", "eduk8s")

frame_ancestors = os.environ.get("FRAME_ANCESTORS", "")

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
            scheduler.cleanup_old_sessions_and_users()
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

    # If we already have workshop environment entries in the database
    # then we don't need to do anything else.

    if Environment.objects.all().count():
        return

    # Determine if there is a maximum session count in force across all
    # workshops as well as a limit on how many registered and anonymous
    # users can run at the same time.

    portal_defaults = TrainingPortal.load()

    portal_defaults.sessions_maximum = training_portal["spec"].get("portal",
            {}).get("sessions", {}).get("maximum", 0)
    portal_defaults.sessions_registered = training_portal["spec"].get("portal",
            {}).get("sessions", {}).get("registered", 0)
    portal_defaults.sessions_anonymous = training_portal["spec"].get("portal",
            {}).get("sessions", {}).get("anonymous", portal_defaults.sessions_registered)

    portal_defaults.save()

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

    default_capacity = training_portal["spec"].get("portal", {}).get("capacity",
            portal_defaults.sessions_maximum)
    default_reserved = training_portal["spec"].get("portal", {}).get("reserved", 1)
    default_initial = training_portal["spec"].get("portal", {}).get("initial",
            default_reserved)
    default_expires = training_portal["spec"].get("portal", {}).get("expires", "0m")
    default_orphaned = training_portal["spec"].get("portal", {}).get("orphaned", "0m")

    sessions_remaining = portal_defaults.sessions_maximum

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

        # When a maximum on the number of sessions allowed is specified we
        # need to ensure that we don't create more than that up front. If
        # the total of initial across all workshops is more than the allowed
        # maximum number of sessions, then it is first come first served
        # as to which get created.

        if portal_defaults.sessions_maximum:
            workshop_initial = min(workshop_initial, sessions_remaining)
            sessions_remaining -= workshop_initial

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

def create_new_session(environment):
    session = initiate_workshop_session(environment)
    transaction.on_commit(lambda: scheduler.create_workshop_session(
            name=session.name))
    return session

def create_reserved_session(environment):
    # If required to have reserved workshop instances, unless we have
    # reached capacity for the workshop environment, or overall maximum
    # number of allowed sessions across all workshops, initiate creation
    # of a new workshop session. Note that this should only be called in
    # circumstance where just deleted a workshop session for the
    # workshop environment. In other words, replacing it.

    if not environment.reserved:
        return

    active_sessions = environment.active_sessions_count()
    reserved_sessions = environment.available_sessions_count()

    if reserved_sessions >= environment.reserved:
        return

    if active_sessions >= environment.capacity:
        return

    portal_defaults = TrainingPortal.load()

    if portal_defaults.sessions_maximum:
        total_sessions = (Session.allocated_sessions().count() +
                Session.available_sessions().count())

        if total_sessions >= portal_defaults.sessions_maximum:
            return

    create_new_session(environment)

def allocate_session_for_user(environment, user, token):
    session = environment.available_session()

    if session:
        if token:
            session.mark_as_pending(user, token)
        else:
            session.mark_as_running(user)

        create_reserved_session(environment)

        return session

def create_session_for_user(environment, user, token):
    if environment.active_sessions_count() >= environment.capacity:
        return

    # We have capacity within what is defined for the workshop environment,
    # but we need to make sure that we have reached any limit on the
    # number of sessions for the whole portal. This can be less than the
    # combined capacity specified for all workshop environments.

    portal_defaults = TrainingPortal.load()

    if portal_defaults.sessions_maximum:
        # Work out the number of overall allocated workshop sessions and
        # see if we can still have any more workshops sessions, and stay
        # under maximum number of allowed sessions.

        allocated_sessions = Session.allocated_sessions()

        if allocated_sessions.count() >= portal_defaults.sessions_maximum:
            return

        # Now see if we can create a new workshop session without needing
        # to kill off a reserved session for a different workshop.

        available_sessions = Session.available_sessions()

        if (allocated_sessions.count() + available_sessions.count() <
                portal_defaults.sessions_maximum):
            return create_new_session(environment).mark_as_pending(user, token)

        # No choice but to first kill off a reserved session for a different
        # workshop. This should target the least active workshop but we are
        # not tracking any statistics yet to do that with certainty, so kill
        # off the oldest session. We kill it off by expiring it immediately
        # and then letting session reaper kick in and delete it. This can
        # take up to 15 seconds.

        available_sessions = available_sessions.order_by("created")

        available_sessions[0].mark_as_stopping()

        # Now create the new workshop session for the required workshop
        # environment.

        return create_new_session(environment).mark_as_pending(user, token)

    else:
        return create_new_session(environment).mark_as_pending(user, token)

def retrieve_session_for_user(environment, user, token=None):
    # Determine if there is already an allocated session for this workshop
    # environment which the user is an owner of. If there is return it.
    # Note that if we have a token because this is being requested via
    # the REST API, it will not overwrite any existing token as we want
    # to reuse the existing one and not generate a new one.

    session = environment.allocated_session_for_user(user)

    if session:
        if token and session.is_pending():
            session.mark_as_pending(user, token)
        return session

    # Determine if the user has already reach the limit on the number of
    # sessions any one user is allowed to run. Note that this only applies
    # to sessions for registered users, excluding admin users. This is
    # because it is assumed that when using the REST API that the number
    # of active sessions is controlled by the front end.

    portal_defaults = TrainingPortal.load()

    if not user.is_staff:
        sessions = Session.allocated_sessions_for_user(user)
        if user.groups.filter(name="anonymous").exists():
            if portal_defaults.sessions_anonymous:
                if sessions.count() >= portal_defaults.sessions_anonymous:
                    return
        else:
            if portal_defaults.sessions_registered:
                if sessions.count() >= portal_defaults.sessions_registered:
                    return

    # Attempt to allocate a session to the user for the workshop environment
    # from any set of reserved sessions.

    session = allocate_session_for_user(environment, user, token)

    if session:
        return session

    # There are no reserved sessions, so we need to trigger the creation
    # of a new session if there is available capacity. If there is no
    # available capacity, no session will be returned.

    return create_session_for_user(environment, user, token)

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
    session_env.append({"name": "TRAINING_PORTAL", "value": portal_name})

    session_env.append({"name": "FRAME_ANCESTORS", "value": frame_ancestors})

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

    google_tracking_id = (
        environment_spec.get("analytics", {}).get("google", {}).get("trackingId")
    )

    if google_tracking_id is not None:
        session_body["spec"]["analytics"] = {"google": {"trackingId": google_tracking_id}}

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
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    now = timezone.now()

    for session in Session.objects.all():
        if not session.is_stopped():
            try:
                custom_objects_api.get_cluster_custom_object(
                    "training.eduk8s.io", "v1alpha1", "workshopsessions",
                    session.name
                )
            except kubernetes.client.rest.ApiException as e:
                if e.status == 404:
                    print(f"Session {session.name} missing. Cleanup session.")
                    scheduler.delete_workshop_session(session)
                    continue

        if session.is_allocated() or session.is_stopping():

            if session.expires and session.expires <= now:
                print(f"Session {session.name} expired. Deleting session.")
                scheduler.delete_workshop_session(session)
            elif session.environment.inactivity:
                try:
                    url = f"{ingress_protocol}://{session.name}.{ingress_domain}/session/activity"
                    r = requests.get(url)
                    if r.status_code == 200:
                        idle_time = timedelta(seconds=r.json()["idle-time"])
                        if idle_time >= session.environment.inactivity:
                            print(f"Session {session.name} orphaned. Deleting session.")
                            scheduler.delete_workshop_session(session)
                except requests.exceptions.ConnectionError:
                    # XXX This can just be because it is slow to start up. Need
                    # a better method to determine if was running but has since
                    # failed in some way and become uncontactable. In that case
                    # right now will only be deleted when workshop timeout
                    # expires if there is one.
                    print(f"WARNING: Cannot connect to workshop session {session.name}.")
                except Exception:
                    print(f"ERROR: Failed to query idle time for workshop session {session.name}.")

                    traceback.print_exc()

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
        else:
            print(f"ERROR: Failed to delete workshop session {session.name}.")

            traceback.print_exc()

    session.mark_as_stopped()

    create_reserved_session(session.environment)

@wrapt.synchronized(scheduler)
@transaction.atomic
def cleanup_old_sessions_and_users():
    # We want to delete records for any sessions older than a certain
    # time, and then remove any anonymous user accounts that have no
    # active sessions and which are older than a certain time.

    cutoff = timezone.now() - timedelta(hours=36)

    sessions = Session.objects.filter(state=SessionState.STOPPED,
            expires__lte=cutoff)

    for session in sessions:
        print(f"Deleting old session {session.name}.")
        session.delete()

    users = User.objects.filter(groups__name="anonymous",
            date_joined__lte=cutoff)

    for user in users:
        sessions = Session.objects.filter(owner=user)

        if not sessions:
            print(f"Deleting anonymous user {user.username}.")
            user.delete()
