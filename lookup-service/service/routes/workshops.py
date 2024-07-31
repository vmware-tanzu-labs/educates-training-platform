"""REST API handlers for workshop requests."""

import logging
import dataclasses

from typing import Any, Dict, List

from aiohttp import web, ClientSession, BasicAuth

from .authnz import login_required, roles_accepted
from ..caches.portals import TrainingPortal
from ..caches.environments import WorkshopEnvironment

from ..caches.databases import ClusterDatabase

logger = logging.getLogger("educates")


async def login_to_portal(session: ClientSession, portal: TrainingPortal) -> str | None:
    """Logs into the specified portal and returns the access token."""

    async with session.post(
        "/oauth2/token/",
        data={
            "grant_type": "password",
            "username": portal.credentials.username,
            "password": portal.credentials.password,
        },
        auth=BasicAuth(portal.credentials.client_id, portal.credentials.client_secret),
    ) as response:
        if response.status != 200:
            logger.error(
                "Failed to login to portal %s of cluster %s.",
                portal.name,
                portal.cluster.name,
            )

            return ""

        login_data = await response.json()

        return login_data.get("access_token")


async def logout_from_portal(
    session: ClientSession, portal: TrainingPortal, access_token: str
) -> None:
    """Logs out of the specified portal."""

    async with session.post(
        "/oauth2/revoke-token/",
        data={
            "client_id": portal.credentials.client_id,
            "client_secret": portal.credentials.client_secret,
            "token": access_token,
        },
    ) as response:
        if response.status != 200:
            logger.error(
                "Failed to logout from portal %s of cluster %s.",
                portal.name,
                portal.cluster.name,
            )


async def fetch_user_sessions_from_portal(
    session: ClientSession, portal: TrainingPortal, user_id: str, access_token
) -> List[Dict[str, Any]]:
    """Fetches the list of active sessions for the specified user from the
    portal."""

    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.get(
        f"/workshops/user/{user_id}/sessions/",
        headers=headers,
    ) as response:
        if response.status != 200:
            logger.error(
                "Failed to get sessions from portal %s of cluster %s for user %s.",
                portal.name,
                portal.cluster.name,
                user_id,
            )

            return []

        data = await response.json()

        return data["sessions"]


async def request_workshop_from_portal(
    session: ClientSession,
    portal: TrainingPortal,
    environment_name: str,
    user_id: str,
    access_token: str,
    index_url: str = "",
) -> str | None:
    """Requests a workshop session from the specified portal and returns the
    activation URL."""

    headers = {"Authorization": f"Bearer {access_token}"}

    async with session.post(
        f"/workshops/environment/{environment_name}/request/",
        headers=headers,
        params={"user": user_id, "index_url": index_url},
    ) as response:
        if response.status != 200:
            logger.error(
                "Failed to request workshop from environment %s of portal %s of cluster %s for user %s.",
                environment_name,
                portal.name,
                portal.cluster.name,
                user_id,
            )

            return None

        data = await response.json()

        return data["url"]


async def find_existing_workshop_session(
    selected_portals: List[TrainingPortal],
    user_id: str,
    workshop_name: str,
    index_url: str = "",
) -> str:
    """Checks each of the portals to see if there is an existing workshop
    session for the specified user and workshop. Will then attempt to fetch
    the activation URL for the existing workshop session and return it."""

    if not user_id:
        return None

    # TODO: We need to request these details from the training portals for now
    # instead of being able to monitor TrainingPortal, WorkshopSession and
    # WorkshopAllocation resources as we need to know the client user ID which
    # is not available in the current implementation of the custom resources.

    for target_portal in selected_portals:
        # Check each portal to see if the user has an existing session for the
        # workshop.

        async with ClientSession(target_portal.url) as session:
            # Login to the portal to get an access token using aiohttp client.

            access_token = await login_to_portal(session, target_portal)

            if access_token is None:
                continue

            try:
                # Request the list of active sessions for the user.

                user_sessions = await fetch_user_sessions_from_portal(
                    session, target_portal, user_id, access_token
                )

                # Search the list of sessions to see if any are for the
                # specified workshop.

                for session_data in user_sessions:
                    if session_data["workshop"] == workshop_name:
                        # We found an existing session. We need to get the URL
                        # for this session from the training portal and return
                        # it to the user.

                        # TODO: We should really check how long before the
                        # session expires and only bother to try and restore it
                        # if more than a certain amount of time is left.

                        activation_url = await request_workshop_from_portal(
                            session,
                            target_portal,
                            session_data["environment"],
                            user_id,
                            access_token,
                            index_url,
                        )

                        if activation_url:
                            return activation_url

            finally:
                # Logout of the portal.

                await logout_from_portal(session, target_portal, access_token)


async def fetch_workshop_environments(
    cluster_database: ClusterDatabase,
    selected_portals: List[TrainingPortal],
    workshop_name: str,
    user_id: str = "",
) -> List[Dict[str, Any]]:
    """Gets the list of workshop environments for the specified workshop."""

    # TODO: We need to request these details from the training portals for now
    # instead of being able to monitor TrainingPortal, WorkshopSession and
    # WorkshopAllocation resources as we need to know any client user ID, plus
    # current state of capacity for training portals, neither of which are
    # available in the current implementation of the custom resources.

    # For each portal hosting the workshop, we need to login to the portal and
    # request the list of all active sessions for the workshop. We need to
    # request workshop environments which are running or stopping as an existing
    # workshop session for a user may be associated with a workshop environment
    # which is stopping.

    workshop_environments = []
    existing_session = None

    for target_portal in selected_portals:
        # Login to the portal to get an access token using aiohttp client.

        async with ClientSession(target_portal.url) as session:
            access_token = await login_to_portal(session, target_portal)

            if access_token is None:
                continue

            try:
                # Make a subsequent request to the portal to get a list of
                # active sessions for the workshop we are interested in. For
                # now don't have any choice but to get all workshops and
                # filter in code to get one we want.

                headers = {"Authorization": f"Bearer {access_token}"}

                async with session.get(
                    "/workshops/catalog/environments/",
                    headers=headers,
                    params={"sessions": "true", "state": ["RUNNING", "STOPPING"]},
                ) as response:
                    if response.status != 200:
                        logger.error(
                            "Failed to get workshops from portal %s of cluster %s.",
                            target_portal.name,
                            target_portal.cluster.name,
                        )

                        continue

                    response_data = await response.json()

                    # Search the list of workshop environments for any which
                    # are for the specified workshop, and for that search the
                    # list of active sessions and see if we can find one for
                    # the supplied user.

                    portal_data = response_data["portal"]
                    environments_data = response_data["environments"]

                    for environment_data in environments_data:
                        environment_name = environment_data["name"]

                        if environment_data["workshop"]["name"] == workshop_name:
                            cluster_config = cluster_database.get_cluster_by_name(
                                target_portal.cluster.name
                            )

                            if not cluster_config:
                                logger.warning(
                                    "Cluster %s not found.", target_portal.cluster.name
                                )

                                continue

                            target_environment = target_portal.get_environment(environment_name)

                            if not target_environment:
                                logger.warning(
                                    "Environment %s for portal %s not found in cluster %s.",
                                    environment_name,
                                    target_portal.name,
                                    target_portal.cluster.name,
                                )

                                continue

                            training_portal = TrainingPortal(
                                name=target_portal.name,
                                uid=target_portal.uid,
                                generation=target_portal.generation,
                                labels=target_portal.labels,
                                cluster=cluster_config,
                                url=target_portal.url,
                                capacity=portal_data["sessions"]["maximum"],
                                allocated=portal_data["sessions"]["allocated"],
                                phase=target_portal.phase,
                                credentials=target_portal.credentials,
                            )

                            workshop_environment = WorkshopEnvironment(
                                name=target_environment.name,
                                generation=target_environment.generation,
                                workshop=target_environment.workshop,
                                title=target_environment.title,
                                description=target_environment.description,
                                labels=target_environment.labels,
                                cluster=cluster_config,
                                portal=training_portal,
                                capacity=environment_data["capacity"],
                                reserved=environment_data["reserved"],
                                allocated=environment_data["allocated"],
                                available=environment_data["available"],
                                phase=target_environment.phase,
                            )

                            workshop_environments.append(workshop_environment)

                            if user_id:
                                sessions_data = environment_data["sessions"]

                                for session_data in sessions_data:
                                    if session_data["user"] == user_id:
                                        # We found an existing session. We need to get the URL for
                                        # this session from the training portal and return it to the
                                        # user.

                                        existing_session = (
                                            target_portal.cluster.name,
                                            target_portal.name,
                                            environment_name,
                                        )

            finally:
                # Logout of the portal.

                await logout_from_portal(session, target_portal, access_token)

    return workshop_environments, existing_session


@login_required
@roles_accepted("admin", "workshop-reader")
async def api_get_v1_workshops(request: web.Request) -> web.Response:
    """Returns a list of workshops available to the user."""

    # Grab tenant name from query string parameters. We need to fail with an
    # error if none is provided.

    tenant_name = request.query.get("tenantName")

    if not tenant_name:
        # We don't require a tenant name for admin users.

        matched_roles = request["matched_roles"]

        if "admin" not in matched_roles:
            return web.Response(text="Missing tenantName query parameter", status=400)

    # Now check whether the client is allowed access to this tenant.

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database

    client = request["remote_client"]

    if tenant_name:
        if tenant_name not in client.tenants:
            return web.Response(text="Client not allowed access to tenant", status=403)

    # Work out the set of portals accessible by the user for this tenant. The
    # tenant name may not be set if the user is an admin. An empty set for
    # accessible portals means that the user has access to all portals.

    if tenant_name:
        tenant = tenant_database.get_tenant_by_name(tenant_name)

        if not tenant:
            return web.Response(text="Tenant not available", status=403)

        accessible_portals = tenant.portals_which_are_accessible()

    else:
        accessible_portals = []

    # Generate the list of workshops available to the user for this tenant which
    # are in a running state. We need to eliminate any duplicates as a workshop
    # may be available through multiple training portals. We use the title and
    # description from the last found so we expect these to be consistent.

    workshops = {}

    for portal in accessible_portals:
        for environment in portal.get_running_environments():
            workshops[environment.workshop] = {
                "name": environment.workshop,
                "title": environment.title,
                "description": environment.description,
                "labels": environment.labels,
            }

    return web.json_response({"workshops": list(workshops.values())})


@login_required
@roles_accepted("admin", "workshop-requestor")
async def api_post_v1_workshops(request: web.Request) -> web.Response:
    """Returns a workshop session for the specified tenant and workshop."""

    data = await request.json()

    tenant = data.get("tenantName")

    user_id = data.get("clientUserId") or ""
    action_id = data.get("clientActionId") or ""  # pylint: disable=unused-variable
    index_url = data.get("clientIndexUrl") or ""

    workshop_name = data.get("workshopName")
    parameters = data.get("workshopParams", [])

    if not tenant:
        return web.Response(text="Missing tenantName", status=400)

    if not workshop_name:
        return web.Response(text="Missing workshopName", status=400)

    # Check that client is allowed access to this tenant.

    client = request["remote_client"]

    if tenant not in client.tenants:
        return web.Response(text="Client not allowed access to tenant", status=403)

    # Find the portals accessible to the tenant which hosts the workshop.

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database
    cluster_database = service_state.cluster_database

    tenant = tenant_database.get_tenant_by_name(tenant)

    if not tenant:
        return web.Response(text="Tenant not available", status=403)

    # Get the list of portals hosting the workshop and calculate the subset
    # that are accessible to the tenant.

    accessible_portals = tenant.portals_which_are_accessible()

    selected_portals = []

    for portal in accessible_portals:
        if portal.hosts_workshop(workshop_name):
            selected_portals.append(portal)

    # If there are no resulting portals, then the workshop is not available to
    # the tenant.

    if not selected_portals:
        return web.Response(text="Workshop not available", status=403)

    # If a user ID is supplied, check each of the portals to see if this user
    # already has a workshop session for this workshop.

    if user_id:
        activation_url = await find_existing_workshop_session(
            selected_portals, user_id, workshop_name, index_url
        )

        if activation_url:
            return web.json_response({"sessionActivationUrl": activation_url})

    environments, existing_session = await fetch_workshop_environments(
        cluster_database,
        selected_portals,
        workshop_name,
        user_id,
    )

    data = {
        "workshop": workshop_name,
        "tenant": tenant.name,
        "environments": [
            dataclasses.asdict(environment) for environment in environments
        ],
        "session": existing_session,
    }

    return web.json_response(data)
