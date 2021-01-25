import traceback
import logging

from datetime import timedelta
from operator import itemgetter
from itertools import islice

import pykube

from django.db import transaction
from django.conf import settings

from .resources import ResourceBody
from .operator import background_task
from .locking import resources_lock
from .sessions import setup_workshop_session, create_workshop_session

from ..models import TrainingPortal, Environment, Workshop

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


def convert_duration_to_seconds(size):
    """Converts a specification of a time duration with units to seconds."""

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
    }

    size = str(size)

    for suffix in multipliers:
        if size.lower().endswith(suffix):
            return int(size[0 : -len(suffix)]) * multipliers[suffix]

    try:
        return int(size)
    except ValueError as exception:
        raise RuntimeError(
            '"%s" is not a time duration. Must be an integer or a string with suffix s, m or h.'
            % size
        ) from exception


def duration_as_timedelta(duration):
    return timedelta(seconds=max(0, convert_duration_to_seconds(duration)))


@background_task
@resources_lock
@transaction.atomic
def create_workshop_environment(environment):
    # Validate that the record of the workshop environment is that it is
    # starting.

    if not environment.is_starting():
        return

    # Retrieve the resource for the workshop definition and ensure we have
    # a record of the current version of it.

    K8SWorkshop = pykube.object_factory(api, "training.eduk8s.io/v1alpha2", "Workshop")

    try:
        k8s_workshop_body = ResourceBody(
            K8SWorkshop.objects(api).get(name=environment.workshop_name).obj
        )

    except pykube.exceptions.ObjectDoesNotExist:
        # Return for now. A retry will be performed later when periodic
        # reconcilation loop is run.

        logging.error("Workshop %s does not exist.", environment.workshop_name)

        return

    except pykube.exceptions.PyKubeError:
        traceback.print_exc()
        return

    k8s_workshop_metadata = k8s_workshop_body.metadata
    k8s_workshop_spec = k8s_workshop_body.spec

    workshop, created = Workshop.objects.get_or_create(
        name=environment.workshop_name,
        uid=k8s_workshop_metadata.uid,
        generation=k8s_workshop_metadata.generation,
    )

    if created:
        workshop.title = k8s_workshop_spec.get("title", "")
        workshop.description = k8s_workshop_spec.get("description", "")
        workshop.vendor = k8s_workshop_spec.get("vendor", "")
        workshop.authors = k8s_workshop_spec.get("authors", []).obj()
        workshop.difficulty = k8s_workshop_spec.get("difficulty", "")
        workshop.duration = k8s_workshop_spec.get("duration", "")
        workshop.tags = k8s_workshop_spec.get("tags", []).obj()
        workshop.logo = k8s_workshop_spec.get("logo", "")
        workshop.url = k8s_workshop_spec.get("url", "")
        workshop.content = k8s_workshop_spec.get("content", []).obj()

    workshop.save()

    environment.workshop = workshop

    portal = environment.portal

    environment.name = f"{portal.name}-w{environment.id:02}"

    # Create the workshop environment resource to deploy it.

    portal = environment.portal

    # env = k8s_workshop_spec.get("env", []).obj()

    environment_body = {
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "kind": "WorkshopEnvironment",
        "metadata": {
            "name": environment.name,
            "labels": {
                "training.eduk8s.io/portal.name": portal.name,
            },
            "ownerReferences": [
                {
                    "apiVersion": "training.eduk8s.io/v1alpha1",
                    "kind": "TrainingPortal",
                    "blockOwnerDeletion": False,
                    "controller": True,
                    "name": portal.name,
                    "uid": portal.uid,
                }
            ],
        },
        "spec": {
            "workshop": {"name": workshop.name},
            "request": {"enabled": False},
            "session": {
                "ingress": {
                    "domain": settings.INGRESS_DOMAIN,
                    "secret": settings.INGRESS_SECRET,
                    "class": settings.INGRESS_CLASS,
                },
                "env": environment.env,
            },
            "environment": {
                "objects": [],
            },
        },
    }

    if settings.GOOGLE_TRACKING_ID is not None:
        environment_body["spec"]["analytics"] = {
            "google": {"trackingId": settings.GOOGLE_TRACKING_ID}
        }

    K8SWorkshopEnvironment = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopEnvironment"
    )

    resource = K8SWorkshopEnvironment(api, environment_body)
    resource.create()

    instance = K8SWorkshopEnvironment.objects(api).get(name=environment.name)

    environment.uid = instance.metadata["uid"]

    environment.mark_as_running()

    environment.save()

    # Since this is a newly created workshop environment, we need to trigger
    # the creation of any initial reserve workshop sessions.

    sessions = []

    for _ in range(environment.initial):
        sessions.append(setup_workshop_session(environment))

    def _schedule_session_creation():
        for session in sessions:
            create_workshop_session(name=session.name).schedule(delay=5.0)

    transaction.on_commit(_schedule_session_creation)


def shutdown_workshop_environments(training_portal, workshops):
    """Mark for deletion any workshop environments which are no longer
    included in the list of workshops for the training portal.

    """

    workshop_names = set(map(itemgetter("name"), workshops))

    environments = training_portal.active_environments()

    for environment in environments:
        if environment.workshop_name not in workshop_names:
            if environment.is_starting():
                # If the workshop environment hasn't yet been provisioned
                # we can mark it as stopped immediately as nothing to delete.

                environment.mark_as_stopped()
            else:
                # The workshop environment was already provisioned first mark
                # it as stopping, and then also mark as stopping any workshop
                # sessions which were being kept in reserve for the workshop
                # environment. We mark the workshop environment as stopping
                # first so that capacity and reserved counts are set to zero.

                environment.mark_as_stopping()

                for session in environment.available_sessions():
                    session.mark_as_stopping()


@background_task
@resources_lock
def delete_workshop_environment(environment):
    """Deletes a workshop environment."""

    K8SWorkshopEnvironment = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopEnvironment"
    )

    try:
        resource = K8SWorkshopEnvironment.objects(api).get(name=environment.name)
        resource.delete()

    except pykube.exceptions.ObjectDoesNotExist:
        pass

    except pykube.exceptions.PyKubeError:
        logging.error("Failed to delete workshop environment %s.", environment.name)

        traceback.print_exc()


@background_task
@resources_lock
@transaction.atomic
def delete_workshop_environments(training_portal):
    # Need to loop over any workshop environments marked as being in the
    # stopping state.

    for environment in training_portal.stopping_environments():
        if (
            environment.available_sessions_count() == 0
            and environment.allocated_sessions_count() == 0
        ):
            delete_workshop_environment(environment).schedule()

            environment.mark_as_stopped()


def update_workshop_environments(training_portal, workshops):
    """Updates configuration of any workshops which already exist."""

    for position, workshop in enumerate(workshops, 1):
        environment = training_portal.current_environment(workshop["name"])

        if environment:
            environment.capacity = workshop["capacity"]
            environment.reserved = workshop["reserved"]
            environment.duration = duration_as_timedelta(workshop["expires"])
            environment.inactivity = duration_as_timedelta(workshop["orphaned"])

            # Only update initial reserved session count if the workshop
            # environment hasn't actually been provisioned yet.

            if environment.is_starting():
                environment.initial = workshop["initial"]

            environment.position = position

            environment.save()


def initiate_workshop_environments(training_portal, workshops):
    """Initiate creation of any workshop environments which don't already
    exist in the list of workshops for the training portal.

    """

    for position, workshop in enumerate(workshops, 1):
        environment = training_portal.current_environment(workshop["name"])

        if environment is None:
            environment = Environment(
                portal=training_portal,
                workshop_name=workshop["name"],
                position=position,
                capacity=workshop["capacity"],
                initial=workshop["initial"],
                reserved=workshop["reserved"],
                duration=duration_as_timedelta(workshop["expires"]),
                inactivity=duration_as_timedelta(workshop["orphaned"]),
                env=workshop["env"],
            )

            environment.save()

            transaction.on_commit(
                lambda instance=environment: create_workshop_environment(
                    instance
                ).schedule()
            )


@background_task
@transaction.atomic
def terminate_reserved_sessions(training_portal):
    """Terminate any reserved workshop sessions which put a workshop
    environment over the count for how many reserved sessions they are
    allowed.

    """

    for environment in training_portal.running_environments():
        excess = max(0, environment.available_sessions_count() - environment.reserved)
        print('EXCESS', excess)
        for session in islice(environment.available_sessions(), 0, excess):
            print('SESSION', session)
            session.mark_as_stopping()


@background_task
@transaction.atomic
def initiate_reserved_sessions(training_portal):
    """Create additional reserved sessions if necessary to satisfied stated
    reserved count for a workshop environment. Don't create a reserved session
    if this would put the workshop environment of the training portal over any
    maximum capacity.

    """

    for environment in training_portal.running_environments():
        excess = max(0, environment.available_sessions_count() - environment.reserved)
        print('EXCESS', excess)
        for session in islice(environment.available_sessions(), 0, excess):
            print('SESSION', session)
            session.mark_as_stopping()


@background_task(delay=15.0, repeat=True)
@transaction.atomic
def start_reconciliation_task(name):
    training_portal = TrainingPortal.objects.get(name=name)

    delete_workshop_environments(training_portal).schedule()

    terminate_reserved_sessions(training_portal).schedule()

    initiate_reserved_sessions(training_portal).schedule()
