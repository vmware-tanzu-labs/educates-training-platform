"""Defines basic functions for managing creation of sessions.

"""

import string
import random

import pykube

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from oauth2_provider.models import Application

from ..models import TrainingPortal, Session, SessionState

api = pykube.HTTPClient(pykube.KubeConfig.from_env())

WorkshopSession = pykube.object_factory(
    api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
)


@transaction.atomic
def create_workshop_session(name):
    # Lookup the workshop session that we need to create and make
    # sure it is still in starting state.

    session = Session.objects.get(name=name)

    if session.state != SessionState.STARTING:
        return

    # Create the WorkshopSession custom resource to trigger creation
    # of the actual workshop session.

    ingress_protocol = settings.INGRESS_PROTOCOL
    ingress_domain = settings.INGRESS_DOMAIN
    ingress_secret = settings.INGRESS_SECRET

    portal_name = settings.PORTAL_NAME

    portal_hostname = settings.PORTAL_HOSTNAME

    frame_ancestors = settings.FRAME_ANCESTORS

    workshop_environment = session.environment

    environment_metadata = workshop_environment.resource["metadata"]
    environment_spec = workshop_environment.resource["spec"]

    session_env = list(environment_spec.get("session", {}).get("env"))
    session_env.append({"name": "PORTAL_CLIENT_ID", "value": session.name})
    session_env.append(
        {"name": "PORTAL_CLIENT_SECRET", "value": session.application.client_secret}
    )
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
            ],
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
        session_body["spec"]["analytics"] = {
            "google": {"trackingId": google_tracking_id}
        }

    resource = WorkshopSession(api, session_body)
    resource.create()

    if session.owner:
        if session.token:
            session.state = SessionState.WAITING
        else:
            session.state = SessionState.RUNNING
    else:
        session.state = SessionState.WAITING

    # Make sure we save the update state of the session.

    session.save()


def setup_workshop_session(workshop_environment, **session_kwargs):
    """Setup database objects pertaining to a new workshop session."""

    environment_status = workshop_environment.resource["status"]["eduk8s"]
    workshop_spec = environment_status["workshop"]["spec"]

    tally = workshop_environment.tally = workshop_environment.tally + 1

    workshop_environment.save()

    session_id = f"s{tally:03}"
    session_name = f"{workshop_environment.name}-{session_id}"

    ingress_protocol = settings.INGRESS_PROTOCOL
    ingress_domain = settings.INGRESS_DOMAIN

    session_hostname = f"{session_name}.{ingress_domain}"

    characters = string.ascii_letters + string.digits
    secret = "".join(random.sample(characters, 32))

    redirect_uris = [f"{ingress_protocol}://{session_hostname}/oauth_callback"]

    redirect_uris.append(
        f"{ingress_protocol}://{session_name}-console.{ingress_domain}/oauth_callback"
    )
    redirect_uris.append(
        f"{ingress_protocol}://{session_name}-editor.{ingress_domain}/oauth_callback"
    )
    redirect_uris.append(
        f"{ingress_protocol}://{session_name}-slides.{ingress_domain}/oauth_callback"
    )
    redirect_uris.append(
        f"{ingress_protocol}://{session_name}-terminal.{ingress_domain}/oauth_callback"
    )

    ingresses = workshop_spec.get("session", {}).get("ingresses", [])

    for ingress in ingresses:
        session_ingress_hostname = f"{session_name}-{ingress['name']}.{ingress_domain}"
        redirect_uris.append(
            f"{ingress_protocol}://{session_ingress_hostname}/oauth_callback"
        )

    User = get_user_model()  # pylint: disable=invalid-name

    eduk8s_user = User.objects.get(username=settings.ADMIN_USERNAME)

    application, _ = Application.objects.get_or_create(
        name=session_name,
        client_id=session_name,
        user=eduk8s_user,
        redirect_uris=" ".join(redirect_uris),
        client_type="public",
        authorization_grant_type="authorization-code",
        client_secret=secret,
        skip_authorization=True,
    )

    session = Session.objects.create(
        name=session_name,
        id=session_id,
        application=application,
        created=session_kwargs.get("started", timezone.now()),
        environment=workshop_environment,
        **session_kwargs,
    )

    return session


def create_new_session(environment):
    session = setup_workshop_session(environment)

    # This is only done after transaction commit so that the deployment of the
    # workshop session will not cause failure of the setup of the database
    # entries for the workshop session. If the deployment subsequently fails
    # user access to the session will fail on a timeout and it should be
    # cleaned up at some point.

    transaction.on_commit(lambda: create_workshop_session(session.name))

    return session


def create_reserved_session(environment):
    # If required to have reserved workshop instances, unless we have reached
    # capacity for the workshop environment, or overall maximum number of
    # allowed sessions across all workshops, initiate creation of a new
    # workshop session. Note that this should only be called in circumstance
    # where just deleted, or allocated a workshop session for the workshop
    # environment. In other words, replacing it.

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
        total_sessions = (
            Session.allocated_sessions().count() + Session.available_sessions().count()
        )

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

        if (
            allocated_sessions.count() + available_sessions.count()
            < portal_defaults.sessions_maximum
        ):
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
