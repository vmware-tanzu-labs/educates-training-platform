"""Defines basic functions for managing creation of workshop sessions.

"""

import string
import random
import logging
import traceback

from itertools import islice

import pykube

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from oauth2_provider.models import Application

from ..models import Session

from .operator import background_task
from .locking import resources_lock
from .analytics import report_analytics_event

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


def update_session_status(name, phase):
    """Update the status of the Kubernetes resource object for the workshop
    session.

    """

    try:
        K8SWorkshopSession = pykube.object_factory(
            api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
        )

        resource = K8SWorkshopSession.objects(api).get(name=name)

        # The status may not exist as yet if not processed by the operator.
        # In this case fill it in and operator will preserve the value when
        # sees associated with a training portal.

        resource.obj.setdefault("status", {}).setdefault("eduk8s", {})["phase"] = phase
        resource.update()

    except pykube.exceptions.ObjectDoesNotExist:
        pass

    except pykube.exceptions.PyKubeError:
        logging.error("Failed to update status of workshop session %s.", name)

        traceback.print_exc()


@background_task
@resources_lock
@transaction.atomic
def create_workshop_session(name):
    """Triggers the deployment of a new workshop session to the cluster."""

    # Lookup the workshop session that we need to create and make sure it is
    # still in starting state.

    session = Session.objects.get(name=name)

    if not session.is_starting():
        return

    # Calculate the additional set of environment variables to configure the
    # workshop session for use with the training portal. These are on top of
    # any environment variables the workshop itself uses.

    environment = session.environment

    session_env = list(environment.env)

    session_env.append({"name": "PORTAL_CLIENT_ID", "value": session.name})
    session_env.append(
        {"name": "PORTAL_CLIENT_SECRET", "value": session.application.client_secret}
    )

    portal_api_url = f"{settings.INGRESS_PROTOCOL}://{settings.PORTAL_HOSTNAME}"

    session_env.append({"name": "PORTAL_API_URL", "value": portal_api_url})
    session_env.append({"name": "SESSION_NAME", "value": session.name})
    session_env.append({"name": "TRAINING_PORTAL", "value": settings.PORTAL_NAME})
    session_env.append({"name": "FRAME_ANCESTORS", "value": settings.FRAME_ANCESTORS})

    if environment.duration or environment.inactivity:
        restart_url = f"{portal_api_url}/workshops/session/{session.name}/delete/"
    else:
        restart_url = f"{portal_api_url}/workshops/catalog/"

    if environment.duration:
        session_env.append({"name": "ENABLE_COUNTDOWN", "value": "true"})

    session_env.append({"name": "RESTART_URL", "value": restart_url})

    # Prepare the body of the resource describing the workshop session.

    session_body = {
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "kind": "WorkshopSession",
        "metadata": {
            "name": session.name,
            "labels": {
                "training.eduk8s.io/portal.name": settings.PORTAL_NAME,
                "training.eduk8s.io/environment.name": session.environment.name,
            },
            "ownerReferences": [
                {
                    "apiVersion": "training.eduk8s.io/v1alpha1",
                    "kind": "WorkshopEnvironment",
                    "blockOwnerDeletion": True,
                    "controller": True,
                    "name": session.environment.name,
                    "uid": session.environment.uid,
                }
            ],
        },
        "spec": {
            "environment": {"name": session.environment.name},
            "session": {
                "id": session.id,
                "username": "",
                "password": "",
                "ingress": {
                    "domain": settings.INGRESS_DOMAIN,
                    "secret": settings.INGRESS_SECRET,
                },
                "env": session_env,
            },
        },
    }

    # If Google analytics tracking ID is provided, this needs to be patched
    # into the resource.

    if settings.GOOGLE_TRACKING_ID is not None:
        session_body["spec"]["analytics"] = {
            "google": {"trackingId": settings.GOOGLE_TRACKING_ID}
        }

    # Create the Kubernetes resource for the workshop session.

    K8SWorkshopSession = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
    )

    resource = K8SWorkshopSession(api, session_body)
    resource.create()

    # Update and save the state of the workshop session database record to
    # indicate it is running or waiting for confirmation on being activated if
    # this session was created via the REST API.

    session.url = (
        f"{settings.INGRESS_PROTOCOL}://{session.name}.{settings.INGRESS_DOMAIN}"
    )

    if session.owner:
        update_session_status(session.name, "Allocated")
        report_analytics_event(session, "Session/Started")
        if session.token:
            session.mark_as_waiting()
        else:
            session.mark_as_running()
    else:
        session.mark_as_waiting()


def setup_workshop_session(environment, **session_kwargs):
    """Setup database objects pertaining to a new workshop session."""

    # Increase tally for number of workshop sessions created for the workshop
    # environment and calculate session name. Ensure changed value for tally
    # is saved.

    tally = environment.tally = environment.tally + 1

    session_id = f"s{tally:03}"
    session_name = f"{environment.name}-{session_id}"

    environment.save()

    # Calculate the set of redirect URIs that the OAuth provider application
    # needs to trust. Needs to be enumerated as can't use a wildcard, As such,
    # need a redirect URI for the main workshop URL, one for each embedded
    # application such as the console, plus one for each ingress as they are
    # proxied via the workshop gateway and so are also covered by OAuth.

    def redirect_uri_for_oauth_callback(suffix=None):
        host = session_name

        if suffix:
            host = f"{host}-{suffix}"

        fqdn = f"{host}.{settings.INGRESS_DOMAIN}"

        url = f"{settings.INGRESS_PROTOCOL}://{fqdn}/oauth_callback"

        return url

    redirect_uris = [
        redirect_uri_for_oauth_callback(),
        redirect_uri_for_oauth_callback("console"),
        redirect_uri_for_oauth_callback("editor"),
        redirect_uri_for_oauth_callback("slides"),
        redirect_uri_for_oauth_callback("terminal"),
    ]

    ingresses = environment.workshop.ingresses

    for ingress in ingresses:
        redirect_uris.append(redirect_uri_for_oauth_callback(ingress["name"]))

    # Create the OAuth provider application record. Each workshop session
    # has a unique application record tied to the URLs for that specific
    # workshop session.

    User = get_user_model()  # pylint: disable=invalid-name

    admin_user = User.objects.get(username=settings.ADMIN_USERNAME)

    characters = string.ascii_letters + string.digits
    secret = "".join(random.sample(characters, 32))

    application, _ = Application.objects.get_or_create(
        name=session_name,
        client_id=session_name,
        user=admin_user,
        redirect_uris=" ".join(redirect_uris),
        client_type="public",
        authorization_grant_type="authorization-code",
        client_secret=secret,
        skip_authorization=True,
    )

    # Create the database record for the workshop session, linking it to
    # the OAuth provider application record.

    session = Session.objects.create(
        name=session_name,
        id=session_id,
        application=application,
        created=session_kwargs.get("started", timezone.now()),
        environment=environment,
        **session_kwargs,
    )

    return session


def create_new_session(environment):
    """Setup a record for the workshop session in the database and schedule
    a task to deploy the workshop session in the cluster.

    """

    session = setup_workshop_session(environment)

    transaction.on_commit(lambda: create_workshop_session(session.name).schedule())

    return session


def replace_reserved_session(environment):
    """If required to have reserved workshop instances, unless we have reached
    capacity for the workshop environment, or overall maximum number of
    allowed sessions across all workshops, initiate creation of a new workshop
    session. Note that this should only be called in circumstance where just
    deleted, or allocated a workshop session for the workshop environment. In
    other words, replacing it.

    """

    # Bail out straight away if no reserved sessions.

    if not environment.reserved:
        return

    # Check that haven't already reached limit on number of reserved sessions.

    if environment.available_sessions_count() >= environment.reserved:
        return

    # Also check that haven't reached capacity. This counts both allocated and
    # reserved sessions.

    if environment.active_sessions_count() >= environment.capacity:
        return

    # Finally need to make sure that haven't reached capacity for the training
    # portal as a whole.

    portal = environment.portal

    if portal.sessions_maximum:
        if portal.active_sessions_count() >= portal.sessions_maximum:
            return

    # Safe to create a new workshop session in reserve.

    create_new_session(environment)


@background_task
@resources_lock
@transaction.atomic
def terminate_reserved_sessions(portal):
    """Terminate any reserved workshop sessions which put a workshop
    environment over the count for how many reserved sessions they are
    allowed.

    """

    # First kill of reserved sessions for each workshop environment where
    # they are over what is allowed for that workshop environment.

    for environment in portal.running_environments():
        excess = max(0, environment.available_sessions_count() - environment.reserved)

        for session in islice(environment.available_sessions(), 0, excess):
            update_session_status(session.name, "Stopping")
            session.mark_as_stopping()

    # Also check that not exceed capacity for the whole training portal. If
    # we are, try and kill of oldest reserved sessions associated with any
    # workshop environment.

    if portal.sessions_maximum != 0:
        excess = max(0, portal.active_sessions_count() - portal.sessions_maximum)

        for session in islice(
            portal.available_sessions().order_by("created"), 0, excess
        ):
            update_session_status(session.name, "Stopping")
            session.mark_as_stopping()


@background_task
@resources_lock
@transaction.atomic
def initiate_reserved_sessions(portal):
    """Create additional reserved sessions if necessary to satisfy stated
    reserved count for a workshop environment. Don't create a reserved session
    if this would put the workshop environment of the training portal over any
    maximum capacity.

    """

    sessions = []

    # Need a different approach when maximum number of sessions defined for
    # the whole training portal. Even in that case, still additionally need to
    # consider capacity of individual workshop environments.

    if portal.sessions_maximum == 0:
        # No global maximum on number of sessions for training portal. In
        # this case can check easch workshop environment independently.

        for environment in portal.running_environments():
            # If reserved sessions not required, skip to next one.

            if environment.reserved == 0:
                continue

            # If already at capacity, skip to next one.

            spare_capacity = environment.capacity - environment.active_sessions_count()

            if spare_capacity <= 0:
                continue

            # If already have required number of reserved sessons, skip to
            # next one.

            spare_reserved = (
                environment.reserved - environment.available_sessions_count()
            )

            if spare_reserved <= 0:
                continue

            # Create required number of reserved sessions ensuring we do not
            # go over capacity for the workshop environment.

            spare_sessions = min(spare_reserved, spare_capacity)

            for _ in range(spare_sessions):
                sessions.append(setup_workshop_session(environment))

    else:
        # Maximum number of sessions for training portal in force, so work out
        # how much spare capacity we currently have for the training portal.
        # If no capacity we can bail out straight away.

        spare_capacity = portal.sessions_maximum - portal.active_sessions_count()

        if spare_capacity <= 0:
            return

        # Now check each separate workshop environment.

        for environment in portal.running_environments():
            # If reserved sessions not required, skip to next one.

            if environment.reserved == 0:
                continue

            # If already have required number of reserved sessons, skip to
            # next one.

            spare_reserved = (
                environment.reserved - environment.available_sessions_count()
            )

            if spare_reserved <= 0:
                continue

            # Create required number of reserved sessions ensuring we do not
            # go over capacity for the workshop environment, but also that
            # this will not put us over capacity for whole training portal.

            spare_sessions = min(
                spare_reserved,
                environment.capacity - environment.active_sessions_count(),
                spare_capacity,
            )

            for _ in range(spare_sessions):
                sessions.append(setup_workshop_session(environment))

                # Reduce count of how much capacity still have for the
                # training portal as a whole.

                spare_capacity -= 1

            # Bail out if reached capacity for the whole training portal.

            if spare_capacity <= 0:
                break

    # Schedule the actual creation of the reserved sessions.

    def _schedule_session_creation():
        for session in sessions:
            create_workshop_session(name=session.name).schedule(delay=5.0)

    transaction.on_commit(_schedule_session_creation)


def allocate_session_for_user(environment, user, token, timeout=None):
    """Allocate a workshop session to the user for the specified workshop
    environment from any reserved workshop sessions. Replace now allocated
    workshop session with a new reserved session if required.

    """

    session = environment.available_session()

    if not session:
        return

    # We will have a token when requested via the REST API. The owner and
    # token is updated in this case but left in pending state until activation
    # of the workshop session is subsequently confirmed. The extra
    # confirmation is needed so can reclaim a session which was abandoned
    # immediately due to not being accessed.

    if token:
        update_session_status(session.name, "Allocating")
        session.mark_as_pending(user, token, timeout)
        report_analytics_event(session, "Session/Pending")
    else:
        update_session_status(session.name, "Allocated")
        session.mark_as_running(user)
        report_analytics_event(session, "Session/Started")

    # See if we need to create a new reserved session to replace the one which
    # was just allocated.

    replace_reserved_session(environment)

    return session


def create_session_for_user(environment, user, token, timeout=None):
    """Create a new workshop session in case there was no existing reserved
    workshop sessions for the specified workshop environment.

    """

    # Check first if not exceeding the capacity of the workshop environment.
    # Using the active session count here, which includes workshop sessions
    # which are in reserve, but we would only usually be called in situation
    # where there weren't any reserved sessions in the first place.

    if environment.active_sessions_count() >= environment.capacity:
        return

    # Next see if there is a maximum number of workshop sessions allowed
    # across the whole training portal. If there isn't we are good to create a
    # new workshop session.

    portal = environment.portal

    if portal.sessions_maximum == 0:
        session = create_new_session(environment)
        if token:
            update_session_status(session.name, "Allocating")
        else:
            update_session_status(session.name, "Allocated")
        session.mark_as_pending(user, token, timeout)
        if not token:
            report_analytics_event(session, "Session/Started")
        else:
            report_analytics_event(session, "Session/Pending")
        return session

    # Check the number of allocated workshop sessions for the whole training
    # portal and see if we can still have any more workshops sessions.

    if portal.allocated_sessions_count() >= portal.sessions_maximum:
        return

    # Now see if we can create a new workshop session without needing to kill
    # off a reserved session for a different workshop. The active sessions
    # count includes reserved sessions as well as allocated sessions.

    if portal.active_sessions_count() < portal.sessions_maximum:
        session = create_new_session(environment)
        if token:
            update_session_status(session.name, "Allocating")
        else:
            update_session_status(session.name, "Allocated")
        session.mark_as_pending(user, token, timeout)
        if not token:
            report_analytics_event(session, "Session/Started")
        else:
            report_analytics_event(session, "Session/Pending")
        return session

    # No choice but to first kill off a reserved session for a different
    # workshop. This should target the least active workshop but we are not
    # tracking any statistics yet to do that with certainty, so kill off the
    # oldest session. We kill it off by expiring it immediately and then
    # letting the session reaper kick in and delete it. There should still be
    # at least one reserved session at this point.

    session = portal.available_sessions().order_by("created")[0]
    update_session_status(session.name, "Stopping")
    session.mark_as_stopping()

    # Now create the new workshop session for the required workshop
    # environment.

    session = create_new_session(environment)
    if token:
        update_session_status(session.name, "Allocating")
    else:
        update_session_status(session.name, "Allocated")
    session.mark_as_pending(user, token, timeout)
    if not token:
        report_analytics_event(session, "Session/Started")
    else:
        report_analytics_event(session, "Session/Pending")
    return session


def retrieve_session_for_user(environment, user, token=None, timeout=None):
    """Determine if there is already an allocated session for this workshop
    environment which the user is an owner of. If there is return it. Note
    that if we have a token because this is being requested via the REST API,
    it will not overwrite any existing token as we want to reuse the existing
    one and not generate a new one.

    """

    session = environment.allocated_session_for_user(user)

    if session:
        if token and session.is_pending():
            session.mark_as_pending(user, token, timeout)
        return session

    # Determine if the user is permitted to create a workshop session.

    portal = environment.portal

    if not portal.session_permitted_for_user(user):
        return

    # Attempt to allocate a session to the user for the workshop environment
    # from any set of reserved sessions.

    session = allocate_session_for_user(environment, user, token, timeout)

    if session:
        return session

    # There are no reserved sessions, so we need to trigger the creation
    # of a new session if there is available capacity. If there is no
    # available capacity, no session will be returned.

    return create_session_for_user(environment, user, token, timeout)
