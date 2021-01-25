"""Defines handlers for the TrainingPortal resource type.

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
from .environments import (
    update_workshop_environments,
    initiate_workshop_environments,
    shutdown_workshop_environments,
    start_reconciliation_task,
)


@transaction.atomic
def initialize_robot_account(resource):
    """Initialize the robot user account if this is the first time the
    training portal has been started up.

    """

    # XXX What if there is a delay in the status being updated by operator.

    status = resource.status.get("eduk8s")

    robot_username = status.get("credentials.robot.username")
    robot_password = status.get("credentials.robot.password")

    robot_client_id = status.get("clients.robot.id")
    robot_client_secret = status.get("clients.robot.secret")

    # Check whether the OAuth application for the robot user already
    # exists. If it exists the robot user has already been created and we
    # don't need to do anything.

    try:
        Application.objects.get_or_create(name="robot@eduk8s")
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


def workshops_configuration(training_portal, resource):
    workshops = copy.deepcopy(resource.spec.get("workshops").obj())

    for workshop in workshops:
        if workshop.get("capacity") is not None:
            workshop.setdefault("reserved", workshop["capacity"])
            workshop.setdefault("initial", workshop["reserved"])
        else:
            workshop["capacity"] = training_portal.default_capacity
            workshop["reserved"] = training_portal.default_reserved
            workshop["initial"] = training_portal.default_initial

        workshop["capacity"] = max(0, workshop["capacity"])
        workshop["reserved"] = max(0, min(workshop["reserved"], workshop["capacity"]))

        workshop["initial"] = max(0, min(workshop["initial"], workshop["capacity"]))
        workshop["initial"] = min(workshop["initial"], workshop["reserved"])

        workshop.setdefault("expires", training_portal.default_expires)
        workshop.setdefault("orphaned", training_portal.default_orphaned)

        workshop.setdefault("env", [])

    return workshops


@transaction.atomic
def process_training_portal(resource):
    """Process the training portal configuration, creating or updating the set
    of workshop environments, and creating or deleting reserved sessions.

    """

    # Grab the configuration for the training portal of the same name,
    # creating it if this is the first time it has been seen.

    metadata = resource.metadata

    training_portal, created = TrainingPortal.objects.get_or_create(name=metadata.name)

    # If the uid does not match then return straight away. This should never
    # occur in practice because the instance of the training portal should be
    # deleted automatically if the custom resource for it is deleted as it
    # will be a child of the custom resource.

    if not created and training_portal.uid != metadata.uid:
        return

    # Ensure that the record of the uid and generation fields are up to date.

    training_portal.uid = metadata.uid
    training_portal.generation = metadata.generation

    # Update the database record for this version of the global configuration
    # settings. Note that the global defaults only come into play when a new
    # workshop environment is first created. They are not applied
    # restrospectively to existing workshop environments which had relied on
    # the global defaults when they were first created.

    spec = resource.spec

    sessions_maximum = spec.get("portal.sessions.maximum", 0)
    sessions_registered = spec.get("portal.sessions.registered", 0)
    sessions_anonymous = spec.get("portal.sessions.anonymous", sessions_registered)

    default_capacity = spec.get("portal.capacity", sessions_maximum)
    default_reserved = spec.get("portal.reserved", 1)
    default_initial = spec.get("portal.initial", default_reserved)
    default_expires = spec.get("portal.expires", 0)
    default_orphaned = spec.get("portal.orphaned", 0)

    training_portal.sessions_maximum = sessions_maximum
    training_portal.sessions_registered = sessions_registered
    training_portal.sessions_anonymous = sessions_anonymous
    training_portal.default_capacity = default_capacity
    training_portal.default_reserved = default_reserved
    training_portal.default_initial = default_initial
    training_portal.default_expires = default_expires
    training_portal.default_orphaned = default_orphaned

    training_portal.save()

    # Calculate the list of workshops, filling in any configuration defaults.

    workshops = workshops_configuration(training_portal, resource)

    # Mark for deletion any workshop environments which are no longer included
    # in the list of workshops for the training portal.

    shutdown_workshop_environments(training_portal, workshops)

    # Update configuration of any workshop environments which already exist.

    update_workshop_environments(training_portal, workshops)

    # Initiate creation of any workshop environments which don't already
    # exist.

    initiate_workshop_environments(training_portal, workshops)


@kopf.on.event(
    "training.eduk8s.io",
    "v1alpha1",
    "trainingportals",
    when=lambda event, name, uid, annotations, **_: name == settings.PORTAL_NAME
    and uid == settings.PORTAL_UID
    and event["type"] in (None, "MODIFIED")
    and annotations.get("training.eduk8s.io/strategy", "") == "v2",
)
def training_portal_event(event, body, **_):
    """This is the key entry point for handling any changes to the
    TrainingPortal resource for the instance of the training portal. It will
    be invoked when the process starts or if the resource is modified. It
    technically should not be invoked when the training portal instance is
    being deleted since the training portal instance in that case should be
    getting shutdown as it is owned by the TrainingPortal resource it
    corresponds to.

    """

    if event["type"] == "DELETED":
        return

    # Wrap up body of the resource to make it easier to work with later.

    resource = ResourceBody(body)

    # If this is the first time the training portal has been started, we
    # need to setup the access for the robot account. Access for the admin
    # user was already done when the database was intialized.

    initialize_robot_account(resource)

    # Process the training portal configuration, creating or updating the set
    # of workshop environments, and creating or deleting reserved sessions.

    process_training_portal(resource)

    # Event type will be None in case that the process has just started up as
    # the training portal resource will always exist at that point. For this
    # case start a background task for performing various reconciliation tasks
    # for the training portal.

    if event["type"] == None:
        start_reconciliation_task(resource.name).schedule()
