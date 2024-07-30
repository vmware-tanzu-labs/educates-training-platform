"""REST API handlers for workshop requests."""

import logging
import dataclasses

from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

from aiohttp import web, ClientSession, BasicAuth

from .authnz import login_required, roles_accepted
from ..caches.tenants import TenantConfiguration
from ..caches.clusters import ClusterDatabase, ClusterConfig
from ..caches.portals import PortalDatabase, PortalState, PortalAuth
from ..caches.environments import EnvironmentDatabase, EnvironmentState

logger = logging.getLogger("educates")


# The bound versions of the training portal and workshop environment resources
# are used to get around current limitations with not having capacity state
# information in the Kubernetes custom resources. We populate these objects
# with the capacity and allocated state of the training portal and workshop
# environment resources respectively from REST API calls against the training
# portals.


@dataclass
class TrainingPortal:
    """Bound version of training portal state."""

    name: str
    uid: str
    generation: int
    labels: Dict[Tuple[str, str], str]
    cluster: str
    url: str
    capacity: int
    allocated: int
    phase: str
    auth: PortalAuth


@dataclass
class WorkshopEnvironment:
    """Bound version of workshop environment state."""

    name: str
    generation: int
    workshop: str
    title: str
    description: str
    labels: Dict[str, str]
    cluster: ClusterConfig
    portal: TrainingPortal
    capacity: int
    reserved: int
    allocated: int
    available: int
    phase: str


def active_workshop_environments(
    environment_database: EnvironmentDatabase, portals: Tuple[str, str]
) -> List[EnvironmentState]:
    """Returns the list of active workshop environments from the specified
    portals. Note that if list of portals is empty, all active workshop
    environments are returned."""

    active_environments = []

    for environment in environment_database.get_environments():
        if environment.phase == "Running" and (
            not portals
            or (environment.cluster.name, environment.portal.name) in portals
        ):
            active_environments.append(environment)

    return active_environments


def portals_hosting_workshop(
    tenant: TenantConfiguration,
    workshop_name: str,
    environment_database: EnvironmentDatabase,
    cluster_database: ClusterDatabase,
    portal_database: PortalDatabase,
) -> List[PortalState]:
    """Retrieve the set of portals hosting a workshop."""

    # First get the list of portals accessible by the tenant.

    accessible_portals = tenant.portals_which_are_accessible(portal_database)

    # Now iterate over the list of workshops and for each workshop check if
    # it is hosted by a portal that is accessible by the tenant.

    selected_portals = []

    for environment in environment_database.get_environments():
        if environment.workshop == workshop_name:
            if (
                environment.cluster.name,
                environment.portal.name,
            ) in accessible_portals:
                portal = portal_database.get_portal(
                    environment.cluster.name, environment.portal.name
                )
                if portal:
                    selected_portals.append(portal)

    return selected_portals


async def fetch_workshop_environments(
    cluster_database: ClusterDatabase,
    environment_database: EnvironmentDatabase,
    selected_portals: List[PortalState],
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
        portal_name = target_portal.name
        cluster_name = target_portal.cluster.name
        portal_url = target_portal.url

        portal_login_url = f"{portal_url}/oauth2/token/"
        portal_logout_url = f"{portal_url}/oauth2/revoke-token/"
        portal_workshops_url = f"{portal_url}/workshops/catalog/environments/"

        portal_client_id = target_portal.auth.client_id
        portal_client_secret = target_portal.auth.client_secret

        portal_username = target_portal.auth.username
        portal_password = target_portal.auth.password

        # Login to the portal to get an access token using aiohttp client.

        async with ClientSession() as session:
            async with session.post(
                portal_login_url,
                data={
                    "grant_type": "password",
                    "username": portal_username,
                    "password": portal_password,
                },
                auth=BasicAuth(portal_client_id, portal_client_secret),
            ) as response:
                if response.status != 200:
                    logger.warning(
                        "Failed to login to portal %s of cluster %s.",
                        portal_name,
                        cluster_name,
                    )

                    continue

                login_data = await response.json()

                access_token = login_data.get("access_token")

                if access_token is None:
                    logger.warning(
                        "No access token returned from portal %s of cluster %s.",
                        portal_name,
                        cluster_name,
                    )

                    continue

                try:
                    # Make a subsequent request to the portal to get a list of
                    # active sessions for the workshop we are interested in. For
                    # now don't have any choice but to get all workshops and
                    # filter in code to get one we want.

                    headers = {"Authorization": f"Bearer {access_token}"}

                    async with session.get(
                        portal_workshops_url,
                        headers=headers,
                        params={"sessions": "true", "state": ["RUNNING", "STOPPING"]},
                    ) as response:
                        if response.status != 200:
                            logger.error(
                                "Failed to get workshops from portal %s of cluster %s.",
                                portal_name,
                                cluster_name,
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
                                    cluster_name
                                )

                                if not cluster_config:
                                    logger.warning(
                                        "Cluster %s not found.", cluster_name
                                    )

                                    continue

                                target_environment = (
                                    environment_database.get_environment(
                                        cluster_name, portal_name, environment_name
                                    )
                                )

                                if not target_environment:
                                    logger.warning(
                                        "Environment %s for portal %s not found in cluster %s.",
                                        environment_name,
                                        portal_name,
                                        cluster_name,
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
                                    auth=target_portal.auth,
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
                                                cluster_name,
                                                portal_name,
                                                environment_name,
                                            )

                finally:
                    # Logout of the portal.

                    async with session.post(
                        portal_logout_url,
                        data={
                            "client_id": portal_client_id,
                            "client_secret": portal_client_secret,
                            "token": access_token,
                        },
                    ) as response:
                        if response.status != 200:
                            logger.error(
                                "Failed to logout from portal %s of cluster %s.",
                                portal_name,
                                cluster_name,
                            )

                        logger.info(
                            "Logged out of portal %s from cluster %s.",
                            portal_name,
                            cluster_name,
                        )

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

    portal_database = service_state.portal_database

    if tenant_name:
        tenant = tenant_database.get_tenant_by_name(tenant_name)

        if not tenant:
            return web.Response(text="Tenant not available", status=403)

        accessible_portals = tenant.portals_which_are_accessible(portal_database)

    else:
        accessible_portals = set()

    # Generate the list of workshops available to the user for this tenant which
    # are in a running state. We need to eliminate any duplicates as a workshop
    # may be available through multiple training portals. We use the title and
    # description from the last found so we expect these to be consistent.

    environment_database = service_state.environment_database

    workshops = {}

    for environment in active_workshop_environments(
        environment_database, accessible_portals
    ):
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
    portal_database = service_state.portal_database
    environment_database = service_state.environment_database

    tenant = tenant_database.get_tenant_by_name(tenant)

    if not tenant:
        return web.Response(text="Tenant not available", status=403)

    selected_portals = portals_hosting_workshop(
        tenant, workshop_name, environment_database, cluster_database, portal_database
    )

    # If there are no hosting portals, then the workshop is not available to
    # the tenant.

    if not selected_portals:
        return web.Response(text="Workshop not available", status=403)

    data = [
        {"name": portal.name, "cluster": portal.cluster.name, "url": portal.url}
        for portal in selected_portals
    ]

    environments, existing_session = await fetch_workshop_environments(
        cluster_database,
        environment_database,
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
