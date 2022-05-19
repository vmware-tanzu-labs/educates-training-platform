"""Defines basic functions for managing creation of workshop environments.

"""

import traceback
import logging
import hashlib

from datetime import timedelta
from operator import itemgetter

import kopf
import pykube

from django.db import transaction
from django.conf import settings

from .resources import ResourceBody
from .operator import background_task
from .locking import resources_lock
from .sessions import (
    update_session_status,
    setup_workshop_session,
    create_workshop_session,
)
from .analytics import report_analytics_event

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
    """Converts a specification of a time duration with units to a timedelta."""

    return timedelta(seconds=max(0, convert_duration_to_seconds(duration)))


def update_environment_status(name, phase):
    """Update the status of the Kubernetes resource object for the workshop
    environment.

    """

    try:
        K8SWorkshopEnvironment = pykube.object_factory(
            api,
            f"training.{settings.OPERATOR_API_GROUP}/v1beta1",
            "WorkshopEnvironment",
        )

        resource = K8SWorkshopEnvironment.objects(api).get(name=name)

        # Can't update status if deployment had stalled due to the workshop
        # definition not existing.

        if (
            resource.obj.get("status", {})
            .get(settings.OPERATOR_STATUS_KEY, {})
            .get("phase")
        ):
            resource.obj["status"][settings.OPERATOR_STATUS_KEY]["phase"] = phase
            resource.update()

    except pykube.exceptions.ObjectDoesNotExist:
        pass

    except pykube.exceptions.PyKubeError:
        logging.error("Failed to update status of workshop environment %s.", name)

        traceback.print_exc()


@background_task
@resources_lock
@transaction.atomic
def activate_workshop_environment(resource):
    """Updates workshop details of a workshop environment and marks the
    workshop environment as being running.

    """

    # Lookup with training portal the workshop environment is associated with.
    # In this case since starting with the workshop environment resource, need
    # to get that from the label added to the resource by the operator.

    try:
        portal = TrainingPortal.objects.get(
            name=resource.metadata.labels.get(
                f"training.{settings.OPERATOR_API_GROUP}/portal.name", ""
            )
        )
    except TrainingPortal.DoesNotExist:
        return

    # The name of the resource is the name of the workshop environment so see
    # if we have a record of such a workshop environment.

    environment = portal.workshop_environment(resource.name)

    if not environment:
        return

    # Double check that has matching uid and not somehow getting event
    # notification for different instance.

    if environment.uid != resource.metadata.uid:
        return

    # Validate that the record of the workshop environment is that it is
    # starting otherwise need to ignore the event.

    if not environment.is_starting():
        return

    # Retrieve the details for the workshop definition and ensure we have a
    # record of the current version of it.

    details = resource.status.get(f"{settings.OPERATOR_STATUS_KEY}.workshop")

    workshop, created = Workshop.objects.get_or_create(
        name=details.get("name"),
        uid=details.get("uid"),
        generation=details.get("generation"),
    )

    logging.info(
        "Activate workshop environment %s for workshop %s, uid %s, generation %s.",
        environment.name,
        workshop.name,
        workshop.uid,
        workshop.generation,
    )

    if created:
        workshop.title = details.get("spec.title", "")
        workshop.description = details.get("spec.description", "")
        workshop.vendor = details.get("spec.vendor", "")
        workshop.authors = details.get("spec.authors", []).obj()
        workshop.difficulty = details.get("spec.difficulty", "")
        workshop.duration = details.get("spec.duration", "")
        workshop.tags = details.get("spec.tags", []).obj()
        workshop.logo = details.get("spec.logo", "")
        workshop.url = details.get("spec.url", "")

        content = dict(details.get("spec.content", {}).obj())

        image = content.get("image", "")
        files = content.get("files", "")
        url = details.get("spec.session.applications.workshop.url", "")

        if url:
            content["url"] = url

        content["id"] = hashlib.md5(
            f"{image}:{files}:{url}".encode("UTF-8")
        ).hexdigest()

        workshop.content = content

        workshop.ingresses = details.get("spec.session.ingresses", []).obj()

    workshop.save()

    # Attach the record of the workshop details to the workshop environment
    # and mark the workshop environment as running. The call to save it is
    # redundant since done when mark it as running, but include it anyway for
    # clarity.

    environment.workshop = workshop

    environment.mark_as_running()

    environment.save()

    # Since this is a newly created workshop environment, we need to trigger
    # the creation of any initial reserved workshop sessions. We need to make
    # sure we don't go over any capacity cap for the training portal as a
    # whole.

    sessions = []

    maximum = portal.sessions_maximum

    if maximum == 0:
        maximum = environment.initial
    else:
        maximum -= portal.active_sessions_count()

    required = min(environment.initial, maximum)

    for _ in range(required):
        sessions.append(setup_workshop_session(environment))

    def _schedule_session_creation():
        for session in sessions:
            create_workshop_session(name=session.name).schedule(delay=5.0)

    transaction.on_commit(_schedule_session_creation)


@kopf.on.event(
    f"training.{settings.OPERATOR_API_GROUP}",
    "v1beta1",
    "workshopenvironments",
    when=lambda event, labels, **_: event["type"] in (None, "MODIFIED")
    and labels.get(f"training.{settings.OPERATOR_API_GROUP}/portal.name", "")
    == settings.PORTAL_NAME,
)
def workshop_environment_event(event, body, **_):  # pylint: disable=unused-argument
    """This is the entrypoint for handling event notifications for the
    WorkshopEnvironment resource. We watch for these so we know when the
    details of a workshop are added to the status of the workshop environment
    resource signalling that the workshop environment has been created. When
    this is seen, use that to progress the state of the workshop environment
    to running.

    """

    # Wrap up body of the resource to make it easier to work with later.

    resource = ResourceBody(body)

    # Check whether the workshop environment status has been updated with the
    # workshop specification.

    if not resource.status.get(f"{settings.OPERATOR_STATUS_KEY}.workshop.uid"):
        return

    # Activate the workshop environment, setting status to running if we can.

    activate_workshop_environment(resource).schedule()


def shutdown_workshop_environments(training_portal, workshops):
    """Mark for deletion any workshop environments which are no longer
    included in the list of workshops for the training portal.

    """

    workshop_names = set(map(itemgetter("name"), workshops))

    environments = training_portal.active_environments()

    for environment in environments:
        if environment.workshop_name not in workshop_names:
            # Mark the workshop environment as stopping. Next mark as stopping
            # any workshop sessions which were being kept in reserve for the
            # workshop environment so that they are deleted. We mark the
            # workshop environment as stopping first so that capacity and
            # reserved counts are set to zero and replacements aren't created.
            # The actual workshop environment as a whole will only be deleted
            # when the number of active sessions reaches zero. If there were
            # allocated workshop sessions, that will only be when they expire.

            logging.info(
                "Stopping workshop environment %s for workshop %s, uid %s, generation %s..",
                environment.name,
                environment.workshop.name,
                environment.workshop.uid,
                environment.workshop.generation,
            )

            update_environment_status(environment.name, "Stopping")
            environment.mark_as_stopping()
            report_analytics_event(environment, "Environment/Terminate")

            for session in environment.available_sessions():
                update_session_status(session.name, "Stopping")
                session.mark_as_stopping()
                report_analytics_event(environment, "Session/Terminate")


@background_task
@resources_lock
def delete_workshop_environment(environment):
    """Deletes a workshop environment. If this is called when there are still
    workshop sessions, they will be forcibly deleted.

    """

    K8SWorkshopEnvironment = pykube.object_factory(
        api, f"training.{settings.OPERATOR_API_GROUP}/v1beta1", "WorkshopEnvironment"
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
    """Looks for workshop environments which are marked as stopping and if
    the number of active workshop sessions has reached zero, the workshop
    environment can safely be deleted without interrupting any users.

    """

    for environment in training_portal.stopping_environments():
        if environment.active_sessions_count() == 0:
            logging.info("Delete workshop environment %s.", environment.name)

            delete_workshop_environment(environment).schedule()
            environment.mark_as_stopped()
            report_analytics_event(environment, "Environment/Deleted")


def update_workshop_environments(training_portal, workshops):
    """Updates configuration of any workshops which already exist."""

    for position, workshop in enumerate(workshops, 1):
        environment = training_portal.environment_for_workshop(workshop["name"])

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


@background_task
@resources_lock
@transaction.atomic
def process_workshop_environment(portal, workshop, position):
    """Creates the workshop environment if necessary, both in the database
    and in Kubernetes.

    """

    # First see if there is already a workshop environment for the workshop.
    # If there is we don't want to be creating a second one.

    environment = portal.environment_for_workshop(workshop["name"])

    if environment:
        return

    # Create initial record for the workshop environment in the database.

    environment = Environment(
        portal=portal,
        workshop_name=workshop["name"],
        position=position,
        capacity=workshop["capacity"],
        initial=workshop["initial"],
        reserved=workshop["reserved"],
        duration=duration_as_timedelta(workshop["expires"]),
        inactivity=duration_as_timedelta(workshop["orphaned"]),
        env=workshop["env"],
    )

    # Save it so that the database record ID is allocated as we use that in
    # the name of the workshop environment. A further save will be done later.

    environment.save()

    environment.name = f"{portal.name}-w{environment.id:02}"

    logging.info(
        "Creating workshop environment %s for workshop %s.",
        environment.name,
        workshop["name"],
    )

    # Create the workshop environment resource to deploy it.

    environment_body = {
        "apiVersion": f"training.{settings.OPERATOR_API_GROUP}/v1beta1",
        "kind": "WorkshopEnvironment",
        "metadata": {
            "name": environment.name,
            "labels": {
                f"training.{settings.OPERATOR_API_GROUP}/portal.name": portal.name,
            },
            "ownerReferences": [
                {
                    "apiVersion": f"training.{settings.OPERATOR_API_GROUP}/v1beta1",
                    "kind": "TrainingPortal",
                    "blockOwnerDeletion": True,
                    "controller": True,
                    "name": portal.name,
                    "uid": portal.uid,
                }
            ],
        },
        "spec": {
            "workshop": {"name": workshop["name"]},
            "request": {"enabled": False},
            "session": {
                "ingress": {
                    "domain": settings.INGRESS_DOMAIN,
                    "secret": settings.INGRESS_SECRET,
                    "class": settings.INGRESS_CLASS,
                },
                "env": environment.env,
            },
            "environment": {"objects": [], "secrets": []},
        },
    }

    if settings.GOOGLE_TRACKING_ID is not None:
        environment_body["spec"]["analytics"] = {
            "google": {"trackingId": settings.GOOGLE_TRACKING_ID}
        }

    # Query back the workshop environment resource so we can retrieve the uid
    # assigned to it by Kubernetes. We will use that to validate events which
    # are received for the workshop environment resource are in fact for the
    # instance we created.

    K8SWorkshopEnvironment = pykube.object_factory(
        api, f"training.{settings.OPERATOR_API_GROUP}/v1beta1", "WorkshopEnvironment"
    )

    resource = K8SWorkshopEnvironment(api, environment_body)
    resource.create()

    instance = K8SWorkshopEnvironment.objects(api).get(name=environment.name)

    environment.uid = instance.metadata["uid"]

    # Finally save the record again. The workshop environment is left in
    # starting state. It will only be progressed to running state when we
    # receive an event for the workshop environment being modified by the
    # operator with the workshop specification filled out in it.

    environment.save()

    report_analytics_event(environment, "Environment/Created")


def initiate_workshop_environments(portal, workshops):
    """Initiate creation of any workshop environments which don't already
    exist in the list of workshops for the training portal.

    """

    # Process each workshop separately as subsequent task so that errors
    # only affect the one workshop.

    for position, workshop in enumerate(workshops, 1):
        process_workshop_environment(portal, workshop, position).schedule()
