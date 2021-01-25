"""Defines cleanup functions for deleting expired workshop sessions and
later deleting historical records of sessions and inactive anonymous users.

"""

import traceback
import logging

from datetime import timedelta

import pykube
import requests

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import SessionState, Session

from .sessions import create_reserved_session
from .locking import resources_lock
from .operator import background_task


api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@background_task(delay=15.0, repeat=True)
@resources_lock
def purge_expired_workshop_sessions():
    """Look for workshop sessions which have expired and delete them."""

    now = timezone.now()

    # Loop over all records of workshop sessions in the database and check
    # whether any should be deleted and/or marked as stopped.

    K8SWorkshopSession = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
    )

    for session in Session.objects.all():
        if not session.is_stopped():
            # If the workshop session hasn't stopped yet, check to see whether
            # there is a deployed workshop session. If there isn't, it means
            # it was deleted manually. In this case trigger a task to clean up
            # the workshop session. In this case there will be no deployment
            # to delete, but still have to mark the workshop session as
            # deleted in the database.

            try:
                K8SWorkshopSession.objects(api).get(name=session.name)

            except pykube.exceptions.ObjectDoesNotExist:
                logging.info("Session %s missing. Cleanup session.", session.name)

                delete_workshop_session(session).schedule()

                continue

            except pykube.exceptions.PyKubeError:
                pass

        if session.is_allocated() or session.is_stopping():
            # If the workshop session is in use, including where it has been
            # explicitly marked for expiration, if expiration time has been
            # reached we need to delete it. If expiration time hasn't been
            # reached and there is an inactivity timeout, check that it hasn't
            # been orhpaned.

            if session.expires and session.expires <= now:
                logging.info("Session %s expired. Deleting session.", session.name)

                delete_workshop_session(session).schedule()

            elif session.environment.inactivity:
                try:
                    # Query the idle time from the workshop session instance.

                    host = f"{session.name}.{settings.INGRESS_DOMAIN}"
                    url = f"{settings.INGRESS_PROTOCOL}://{host}/session/activity"

                    response = requests.get(url)

                    if response.status_code == 200:
                        # If got a response and we have exceeded the
                        # inactivity timeout then trigger deletion of the
                        # workshop session.

                        idle_time = timedelta(seconds=response.json()["idle-time"])

                        if idle_time >= session.environment.inactivity:
                            logging.info(
                                "Session %s orphaned. Deleting session.", session.name
                            )

                            delete_workshop_session(session).schedule()

                    else:
                        # XXX If we don't get a valid response then not
                        # currently doing anything. Need a better method to
                        # determine if was running but has since failed in
                        # some way and become uncontactable. In that case
                        # right now will only be deleted when workshop timeout
                        # expires if there is one.

                        pass

                except requests.exceptions.ConnectionError:
                    # XXX This can just be because it is slow to start up.
                    # Need a better method to determine if was running but has
                    # since failed in some way and become uncontactable. In
                    # that case right now will only be deleted when workshop
                    # timeout expires if there is one.

                    logging.warning(
                        "Cannot connect to workshop session %s.", session.name
                    )

                except Exception:  # pylint: disable=broad-except
                    # Not aware of circumstances where would get an unexpected
                    # exception, but need to log and ignore it as we don't
                    # want to stop looping over all sessions.

                    logging.error(
                        "Failed to query idle time for workshop session %s.",
                        session.name,
                    )

                    traceback.print_exc()


@background_task
@resources_lock
def delete_workshop_session(session):
    """Deletes a workshop session."""

    # First attempt to delete the deployment of the workshop session. It
    # doesn't matter if it doesn't exist. That situation can arise where
    # the workshop session was deleted manually for some reason.

    K8SWorkshopSession = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
    )

    try:
        resource = K8SWorkshopSession.objects(api).get(name=session.name)
        resource.delete()

    except pykube.exceptions.ObjectDoesNotExist:
        pass

    except pykube.exceptions.PyKubeError:
        logging.error("Failed to delete workshop session %s.", session.name)

        traceback.print_exc()

    # Update the workshop session as stopped in the database, then see
    # whether a new workshop session needs to be created in its place as
    # a reserved session.

    with transaction.atomic():
        session.mark_as_stopped()

        create_reserved_session(session.environment)


@background_task(delay=15.0, repeat=True)
@resources_lock
def cleanup_old_sessions_and_users():
    """Delete records for any sessions older than a certain time, and then
    remove any anonymous user accounts that have no active sessions and which
    are older than a certain time.

    """

    with transaction.atomic():
        # Delete record of workshop sessions more than 36 hours old.

        cutoff = timezone.now() - timedelta(hours=36)

        sessions = Session.objects.filter(
            state=SessionState.STOPPED, expires__lte=cutoff
        )

        for session in sessions:
            logging.info("Deleting old session %s.", session.name)
            session.delete()

        # Delete any anonymous users older than 36 hours old, which
        # now don't have any workshop sessions associated with them.

        User = get_user_model()  # pylint: disable=invalid-name

        users = User.objects.filter(groups__name="anonymous", date_joined__lte=cutoff)

        for user in users:
            sessions = Session.objects.filter(owner=user)

            if not sessions:
                logging.info("Deleting anonymous user %s.", user.username)
                user.delete()
