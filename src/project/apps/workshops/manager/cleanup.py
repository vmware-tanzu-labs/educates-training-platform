"""Defines cleanup functions for deleting expired workshop sessions and
later deleting historical records of sessions and inactive anonymous users.

"""

import asyncio
import traceback

from datetime import timedelta

import pykube
import requests

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import SessionState, Session

from .sessions import create_reserved_session
from .locking import scheduler_lock
from .operator import event_loop


api = pykube.HTTPClient(pykube.KubeConfig.from_env())

WorkshopSession = pykube.object_factory(
    api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
)


@scheduler_lock
def purge_expired_workshop_sessions():
    print("INFO: Executing purge_expired_workshop_sessions().")

    now = timezone.now()

    ingress_protocol = settings.INGRESS_PROTOCOL
    ingress_domain = settings.INGRESS_DOMAIN

    async def execute_delete_workshop_session(session):
        delete_workshop_session(session)

    for session in Session.objects.all():
        if not session.is_stopped():
            try:
                WorkshopSession.objects(api).get(name=session.name)

            except pykube.exceptions.ObjectDoesNotExist:
                print(f"Session {session.name} missing. Cleanup session.")

                asyncio.run_coroutine_threadsafe(
                    execute_delete_workshop_session(session), event_loop()
                )

                continue

            except pykube.exceptions.PyKubeError:
                pass

        if session.is_allocated() or session.is_stopping():
            if session.expires and session.expires <= now:
                print(f"Session {session.name} expired. Deleting session.")

                asyncio.run_coroutine_threadsafe(
                    execute_delete_workshop_session(session), event_loop()
                )

            elif session.environment.inactivity:
                try:
                    url = f"{ingress_protocol}://{session.name}.{ingress_domain}/session/activity"
                    r = requests.get(url)
                    if r.status_code == 200:
                        idle_time = timedelta(seconds=r.json()["idle-time"])
                        if idle_time >= session.environment.inactivity:
                            print(f"Session {session.name} orphaned. Deleting session.")

                            asyncio.run_coroutine_threadsafe(
                                execute_delete_workshop_session(session), event_loop()
                            )

                except requests.exceptions.ConnectionError:
                    # XXX
                    # This can just be because it is slow to start up. Need
                    # a better method to determine if was running but has since
                    # failed in some way and become uncontactable. In that case
                    # right now will only be deleted when workshop timeout
                    # expires if there is one.

                    print(
                        f"WARNING: Cannot connect to workshop session {session.name}."
                    )

                except Exception: # pylint: disable=broad-except
                    print(
                        f"ERROR: Failed to query idle time for workshop session {session.name}."
                    )

                    traceback.print_exc()


@scheduler_lock
def delete_workshop_session(session):
    try:
        resource = WorkshopSession.objects(api).get(name=session.name)
        resource.delete()

    except pykube.exceptions.ObjectDoesNotExist:
        pass

    except pykube.exceptions.PyKubeError:
        print(f"ERROR: Failed to delete workshop session {session.name}.")

        traceback.print_exc()

    with transaction.atomic():
        session.mark_as_stopped()

        create_reserved_session(session.environment)


def cleanup_old_sessions_and_users():
    """Delete records for any sessions older than a certain time, and then
    remove any anonymous user accounts that have no active sessions and which
    are older than a certain time.

    """

    print("INFO: Executing cleanup_old_sessions_and_users().")

    try:
        with transaction.atomic():
            # Delete record of workshop sessions more than 36 hours old.

            cutoff = timezone.now() - timedelta(hours=36)

            sessions = Session.objects.filter(
                state=SessionState.STOPPED, expires__lte=cutoff
            )

            for session in sessions:
                print(f"Deleting old session {session.name}.")
                session.delete()

            # Delete any anonymous users older than 36 hours old, which
            # now have an workshop sessions associated with them.

            User = get_user_model()  # pylint: disable=invalid-name

            users = User.objects.filter(
                groups__name="anonymous", date_joined__lte=cutoff
            )

            for user in users:
                sessions = Session.objects.filter(owner=user)

                if not sessions:
                    print(f"Deleting anonymous user {user.username}.")
                    user.delete()

    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()
