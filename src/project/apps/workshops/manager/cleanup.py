"""Defines cleanup functions for deleting expired workshop sessions and
later deleting historical records of sessions and inactive anonymous users.

"""

import traceback

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import SessionState, Session


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

            User = get_user_model() # pylint: disable=invalid-name

            users = User.objects.filter(
                groups__name="anonymous", date_joined__lte=cutoff
            )

            for user in users:
                sessions = Session.objects.filter(owner=user)

                if not sessions:
                    print(f"Deleting anonymous user {user.username}.")
                    user.delete()

    except Exception: # pylint: disable=broad-except
        traceback.print_exc()
