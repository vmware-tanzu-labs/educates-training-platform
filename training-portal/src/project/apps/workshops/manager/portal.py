"""Defines handlers for the TrainingPortal resource type. The whole structure
of the application is actually setup to be able to handle multiple training
portal instances, but we gate on just the name of the one that this specific
process instance is for.

"""

import copy

import kopf

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from oauth2_provider.models import Application

from ..models import TrainingPortal

from .resources import ResourceBody
from .operator import background_task, initialize_kopf
from .locking import resources_lock
from .environments import (
    update_workshop_environments,
    initiate_workshop_environments,
    shutdown_workshop_environments,
    delete_workshop_environments,
    update_environment_status,
    process_workshop_environment,
)
from .sessions import (
    initiate_reserved_sessions,
    terminate_reserved_sessions,
    update_session_status,
)
from .cleanup import cleanup_old_sessions_and_users, purge_expired_workshop_sessions


@resources_lock
@transaction.atomic
def initialize_robot_account(resource):
    """Initialize the robot user account if this is the first time the
    training portal has been started up.

    """

    status = resource.status.get("eduk8s")

    robot_username = status.get("credentials.robot.username")
    robot_password = status.get("credentials.robot.password")

    robot_client_id = status.get("clients.robot.id")
    robot_client_secret = status.get("clients.robot.secret")

    # Check whether the OAuth application for the robot user already
    # exists. If it exists the robot user has already been created and we
    # don't need to do anything.

    try:
        Application.objects.get(name="robot@eduk8s")
    except Application.DoesNotExist:
        pass
    else:
        return

    # Create the robot user and add it to a robots group.

    User = get_user_model()  # pylint: disable=invalid-name

    user = User.objects.create_user(robot_username, password=robot_password)

    group, _ = Group.objects.get_or_create(name="robots")
    user.groups.add(group)
    user.save()

    # Create the application object for OAuth access.

    Application.objects.get_or_create(
        name="robot@eduk8s",
        client_id=robot_client_id,
        user=user,
        client_type="public",
        authorization_grant_type="password",
        client_secret=robot_client_secret,
    )


def workshop_configuration(portal, workshop):
    """Returns santized configuration for single workshop from the training
    portal resource definition. Any fields which were not set will be field
    out with defaults.

    """

    workshop = copy.deepcopy(workshop)

    if workshop.get("capacity") is None:
        workshop["capacity"] = portal.default_capacity

    if workshop.get("reserved") is None:
        if portal.default_reserved is not None:
            workshop["reserved"] = portal.default_reserved
        else:
            workshop["reserved"] = 1

    if workshop.get("initial") is None:
        if portal.default_initial is not None:
            workshop["initial"] = portal.default_initial
        else:
            workshop["initial"] = workshop["reserved"]

    workshop["capacity"] = max(0, workshop["capacity"])
    workshop["reserved"] = max(0, min(workshop["reserved"], workshop["capacity"]))

    workshop["initial"] = max(0, min(workshop["initial"], workshop["capacity"]))
    workshop["initial"] = min(workshop["initial"], workshop["reserved"])

    workshop.setdefault("expires", portal.default_expires)
    workshop.setdefault("orphaned", portal.default_orphaned)

    workshop.setdefault("env", [])

    return workshop


def workshops_configuration(portal, resource):
    """Returns santized configuration for the workshops from the training
    portal resource definition. Any fields which were not set will be field
    out with defaults.

    """

    workshops = []

    for workshop in resource.spec.get("workshops").obj():
        workshops.append(workshop_configuration(portal, workshop))

    return workshops


@resources_lock
@transaction.atomic
def process_training_portal(resource):
    """Process the training portal configuration, creating or updating the set
    of workshop environments, and creating or deleting reserved sessions.

    """

    # Grab the configuration for the training portal of the same name,
    # creating it if this is the first time it has been seen.

    metadata = resource.metadata

    portal, created = TrainingPortal.objects.get_or_create(name=metadata.name)

    # If the uid does not match then return straight away. This should never
    # occur in practice because the instance of the training portal should be
    # deleted automatically if the custom resource for it is deleted as it
    # will be a child of the custom resource.

    if not created and portal.uid != metadata.uid:
        return

    # Ensure that the record of the uid and generation fields are up to date.

    portal.uid = metadata.uid
    portal.generation = metadata.generation

    # Update the database record for this version of the global configuration
    # settings. Note that the global defaults only come into play when a new
    # workshop environment is first created. They are not applied
    # restrospectively to existing workshop environments which had relied on
    # the global defaults when they were first created.

    spec = resource.spec

    sessions_maximum = spec.get("portal.sessions.maximum", 0)
    sessions_registered = spec.get("portal.sessions.registered", 0)
    sessions_anonymous = spec.get("portal.sessions.anonymous", sessions_registered)

    portal.sessions_maximum = sessions_maximum
    portal.sessions_registered = sessions_registered
    portal.sessions_anonymous = sessions_anonymous

    default_capacity = spec.get("portal.capacity", sessions_maximum)
    default_reserved = spec.get("portal.reserved")
    default_initial = spec.get("portal.initial", default_reserved)
    default_expires = spec.get("portal.expires", "0")
    default_orphaned = spec.get("portal.orphaned", "0")

    portal.default_capacity = default_capacity
    portal.default_reserved = default_reserved
    portal.default_initial = default_initial
    portal.default_expires = default_expires
    portal.default_orphaned = default_orphaned

    analytics_url = spec.get("analytics.webhook.url")

    portal.analytics_url = analytics_url

    update_workshop = spec.get("portal.updates.workshop", False)

    portal.update_workshop = update_workshop

    portal.save()

    # Calculate the list of workshops, filling in any configuration defaults.

    workshops = workshops_configuration(portal, resource)

    # Mark for deletion any workshop environments which are no longer included
    # in the list of workshops for the training portal.

    shutdown_workshop_environments(portal, workshops)

    # Update configuration of any workshop environments which already exist.

    update_workshop_environments(portal, workshops)

    # Initiate creation of any workshop environments which don't already
    # exist.

    initiate_workshop_environments(portal, workshops)


@background_task(delay=15.0, repeat=True)
@resources_lock
@transaction.atomic
def start_reconciliation_task(name):
    """Periodic reconcilliation task which ensures current deployments of
    workshop environments and workshop sessions matches desired configuration.

    """

    # Need to guard against the training portal configuration not having been
    # read in as yet. This should only arise if there is a serious issues with
    # updates to resources not being prompt.

    try:
        portal = TrainingPortal.objects.get(name=name)
    except TrainingPortal.DoesNotExist:
        return

    # Queue further task to look for workshop environments that need to be
    # deleted as removed from training portal workshop list.

    delete_workshop_environments(portal).schedule()

    # Queue further task to look for reserved workshop sessions that need to
    # be deleted as required reserved sessions or capacity of workshop
    # environment or training portal was changed.

    terminate_reserved_sessions(portal).schedule()

    # Queue further task to look for where additional workshop sessions need
    # to be created in reserved as required reserved sessions or capacity of
    # workshop environment or training portal was changed.

    initiate_reserved_sessions(portal).schedule()

    purge_expired_workshop_sessions().schedule()

    cleanup_old_sessions_and_users().schedule()


@kopf.on.event(
    "training.eduk8s.io",
    "v1alpha1",
    "trainingportals",
    when=lambda event, name, uid, annotations, **_: name == settings.PORTAL_NAME
    and uid == settings.PORTAL_UID
    and event["type"] in (None, "MODIFIED"),
)
@transaction.atomic
def training_portal_event(event, name, body, **_):
    """This is the key entry point for handling any changes to the
    TrainingPortal resource for the instance of the training portal. It will
    be invoked when the process starts or if the resource is modified. It
    technically should not be invoked when the training portal instance is
    being deleted since the training portal instance in that case should be
    getting shutdown as it is owned by the TrainingPortal resource it
    corresponds to. Note that is gated on specific name of the training
    portal assigned to this process instance.

    """

    # Event type will be None in case that the process has just started up as
    # the training portal resource will always exist at that point. For this
    # case start a background task for performing various reconciliation tasks
    # for the training portal.

    if event["type"] is None:
        start_reconciliation_task(name).schedule()

    # Wrap up body of the resource to make it easier to work with later.

    resource = ResourceBody(body)

    # Ensure that status has been filled out and we can start processing. If
    # it isn't, we should get a subsequent event with the changes.

    if not resource.status.get("eduk8s"):
        return

    # If this is the first time the training portal has been started, we
    # need to setup the access for the robot account. Access for the admin
    # user was already done when the database was intialized.

    initialize_robot_account(resource)

    # Process the training portal configuration, creating or updating the set
    # of workshop environments, and creating or deleting reserved sessions.

    process_training_portal(resource)


@kopf.on.event(
    "training.eduk8s.io",
    "v1alpha2",
    "workshops",
    when=lambda event, labels, **_: event["type"] in (None, "ADDED", "MODIFIED"),
)
@transaction.atomic
def workshop_event(event, body, **_):  # pylint: disable=unused-argument
    """This entry point is for monitoring if Workshop definitions used by any
    workshop environment change. If automatic updates are enabled for changes
    to workshop definition, the existing workshop environment will be stopped
    and replaced with a new workshop environment using the new workshop
    definition. Note that removal of a workshop definition does not result in
    a workshop environment being removed.

    """

    # Wrap up body of the resource to make it easier to work with later.

    resource = ResourceBody(body)

    # Look up the training portal. During startup it may not be ready yet
    # so retry the operation after a delay.

    try:
        portal = TrainingPortal.objects.get(name=settings.TRAINING_PORTAL)
    except TrainingPortal.DoesNotExist:
        raise kopf.TemporaryError("Training portal is not yet ready.", delay=30)

    # Check whether updating workshop environments on changes to a workshop
    # definition is enabled.

    if not portal.update_workshop:
        return

    # Find any workshop environment which is starting up or running which
    # uses the workshop definition. Note that the workshop may not yet
    # have been linked to the environment so need to also check for that.

    environment = portal.environment_for_workshop(resource.name)

    if not environment or not environment.workshop:
        return

    # If the workshop definition identity and generation are the same we do
    # not need to do anything.

    if (
        environment.workshop.uid == resource.metadata.uid
        and environment.workshop.generation == resource.metadata.generation
    ):
        return

    # We need to fake up the workshop entry from the training portal based on
    # the existing workshop environment. We will use the same index position
    # for the workshop entry in the training portal. Do this before marking
    # the existing one as stopping as it clears various values.

    workshop = {
        "name": resource.name,
        "capacity": environment.capacity,
        "initial": environment.initial,
        "reserved": environment.reserved,
        "expires": int(environment.duration.total_seconds()),
        "orphaned": int(environment.inactivity.total_seconds()),
        "env": environment.env,
    }

    position = environment.position

    # Mark the workshop environment as stopping. Next mark as stopping
    # any workshop sessions which were being kept in reserve for the
    # workshop environment so that they are deleted. We mark the
    # workshop environment as stopping first so that capacity and
    # reserved counts are set to zero and replacements aren't created.
    # The actual workshop environment as a whole will only be deleted
    # when the number of active sessions reaches zero. If there were
    # allocated workshop sessions, that will only be when they expire.

    update_environment_status(environment.name, "Stopping")
    environment.mark_as_stopping()

    for session in environment.available_sessions():
        update_session_status(session.name, "Stopping")
        session.mark_as_stopping()

    # Now schedule creation of the replacement workshop session.

    process_workshop_environment(portal, workshop, position).schedule()

    pass


def initialize_portal():
    initialize_kopf()