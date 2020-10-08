import os
import time
import string
import random
import traceback
import asyncio
import contextlib

from datetime import timedelta

from threading import Thread, Lock, Event
from queue import Queue, Empty

import requests

import wrapt

import kopf

import kubernetes
import kubernetes.client

import mod_wsgi

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils import timezone

from oauth2_provider.models import Application

from ..models import TrainingPortal, Workshop, SessionState, Session, Environment

from .resources import ResourceBody
from .operator import initialize_kopf, event_loop, periodic_task
from .locking import scheduler_lock

from .sessions import (
    setup_workshop_session,
    create_workshop_session,
    create_reserved_session,
)

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


scheduler = Scheduler()


def worker():
    while True:
        try:
            item = worker_queue.get(timeout=15)
        except Empty:
            # scheduler.purge_expired_workshop_sessions()
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

        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()

        worker_queue.task_done()


manager_thread = Thread(target=worker)


def shutdown_handler(*_, **__):
    worker_queue.put(None)
    manager_thread.join()


def initialize():
    mod_wsgi.subscribe_shutdown(shutdown_handler)  # pylint: disable=no-member

    manager_thread.start()

    initialize_kopf()

    # Register period tasks with event loop.

    loop = event_loop()

    # Schedule periodic tasks.

    from .cleanup import cleanup_old_sessions_and_users, purge_expired_workshop_sessions

    loop.create_task(periodic_task(purge_expired_workshop_sessions, 15.0))
    loop.create_task(periodic_task(cleanup_old_sessions_and_users, 15.0))


def delay_execution(delay):
    # Force a delay in processing of actions. Only use this during the
    # initial startup to trigger retry waiting for training portal.

    time.sleep(delay)


def convert_duration_to_seconds(size):
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
    }

    size = str(size)

    for suffix in multipliers:
        if size.lower().endswith(suffix):
            return int(size[0 : -len(suffix)]) * multipliers[suffix]

    if size.lower().endswith("b"):
        return int(size[0:-1])

    try:
        return int(size)
    except ValueError:
        raise RuntimeError(
            '"%s" is not a time duration. Must be an integer or a string with suffix s, m or h.'
            % size
        )


@kopf.on.event(
    "training.eduk8s.io",
    "v1alpha1",
    "trainingportals",
    when=lambda name, **_: name == settings.PORTAL_NAME,
)
def my_event_handler(event, body, **_):
    if event["type"] is None:
        handle_training_portal(ResourceBody(body))


def handle_training_portal(training_portal):
    spec = training_portal.spec
    status = training_portal.status.get("eduk8s")

    # If we already have workshop environment entries in the database
    # then we don't need to do anything else.

    if Environment.objects.all().count():
        return

    # Determine if there is a maximum session count in force across all
    # workshops as well as a limit on how many registered and anonymous
    # users can run at the same time.

    portal_defaults = TrainingPortal.load()

    portal_defaults.sessions_maximum = spec.get("portal.sessions.maximum", 0)
    portal_defaults.sessions_registered = spec.get("portal.sessions.registered", 0)
    portal_defaults.sessions_anonymous = spec.get(
        "portal.sessions.anonymous", portal_defaults.sessions_registered
    )

    portal_defaults.save()

    # Ensure that external access setup for robot user account.

    robot_username = status.get("credentials.robot.username")
    robot_password = status.get("credentials.robot.password")

    robot_client_id = status.get("clients.robot.id")
    robot_client_secret = status.get("clients.robot.secret")

    User = get_user_model()  # pylint: disable=invalid-name

    try:
        user = User.objects.get(username=robot_username)
    except User.DoesNotExist:
        user = User.objects.create_user(robot_username, password=robot_password)

    group, _ = Group.objects.get_or_create(name="robots")

    user.groups.add(group)

    user.save()

    Application.objects.get_or_create(
        name="robot@eduk8s",
        client_id=robot_client_id,
        user=user,
        client_type="public",
        authorization_grant_type="password",
        client_secret=robot_client_secret,
    )

    # Ensure that database entries exist for each workshop used.

    workshops = status.get("workshops", [])

    for workshop in workshops:
        Workshop.objects.get_or_create(**workshop.obj())

    # Get the list of workshop environments from the status and schedule
    # processing of each one.

    environments = status.get("environments", [])

    default_capacity = spec.get("portal.capacity", portal_defaults.sessions_maximum)
    default_reserved = spec.get("portal.reserved", 1)
    default_initial = spec.get("portal.initial", default_reserved)
    default_expires = spec.get("portal.expires", "0m")
    default_orphaned = spec.get("portal.orphaned", "0m")

    sessions_remaining = portal_defaults.sessions_maximum

    for environment in environments:
        workshop = Workshop.objects.get(name=environment.get("workshop.name"))

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

        duration = timedelta(
            seconds=max(0, convert_duration_to_seconds(workshop_expires))
        )
        inactivity = timedelta(
            seconds=max(0, convert_duration_to_seconds(workshop_orphaned))
        )

        scheduler.process_workshop_environment(
            name=environment["name"],
            workshop=workshop,
            capacity=workshop_capacity,
            initial=workshop_initial,
            reserved=workshop_reserved,
            duration=duration,
            inactivity=inactivity,
        )


@scheduler_lock
@transaction.atomic
def process_workshop_environment(
    name, workshop, capacity, initial, reserved, duration, inactivity
):
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
        scheduler.process_workshop_environment(
            name=name,
            workshop=workshop,
            capacity=capacity,
            initial=initial,
            reserved=reserved,
            duration=duration,
            inactivity=inactivity,
        )
        print(f"WARNING: Workshop environment {name} is not ready.")
        return

    # See if we already have a entry in the database for the workshop
    # environment, meaning we have already processed it, and do not need
    # to try again. Otherwise a database entry gets created.

    workshop_environment, created = Environment.objects.get_or_create(
        name=name,
        workshop=workshop,
        capacity=capacity,
        initial=initial,
        reserved=reserved,
        duration=duration,
        inactivity=inactivity,
        resource=workshop_environment_k8s,
    )

    if not created:
        return

    # Since this is first time we have seen the workshop environment,
    # we need to trigger the creation of the workshop sessions.

    sessions = []

    for _ in range(initial):
        sessions.append(setup_workshop_session(workshop_environment))

    def _schedule_session_creation():
        for session in sessions:
            scheduler.run_create_workshop_session(name=session.name)

    transaction.on_commit(_schedule_session_creation)


def run_create_workshop_session(name):
    create_workshop_session(name)
