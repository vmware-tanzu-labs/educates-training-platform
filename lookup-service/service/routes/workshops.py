"""REST API handlers for workshop requests."""

from typing import List, Tuple

from aiohttp import web

from .authnz import login_required, roles_accepted
from ..caches.tenants import TenantConfiguration
from ..caches.clusters import ClusterDatabase
from ..caches.portals import PortalDatabase, PortalState
from ..caches.workshops import WorkshopDatabase, WorkshopDetails


def currently_running_workshops(
    workshop_database: WorkshopDatabase, portals: Tuple[str, str]
) -> List[WorkshopDetails]:
    """Returns the list of currently running workshops from the specified
    portals. Note that if list of portals is empty, all running workshops are
    returned."""

    running_workshops = []

    for workshop in workshop_database.get_workshops():
        if workshop.phase == "Running" and (
            not portals or (workshop.cluster, workshop.portal) in portals
        ):
            running_workshops.append(workshop)

    return running_workshops


def portals_hosting_workshop(
    tenant: TenantConfiguration,
    workshop_name: str,
    workshop_database: WorkshopDatabase,
    cluster_database: ClusterDatabase,
    portal_database: PortalDatabase,
) -> List[PortalState]:
    """Retrieve the set of portals hosting a workshop."""

    # First get the list of portals accessible by the tenant.

    accessible_portals = tenant.portals_which_are_accessible(
        cluster_database, portal_database
    )

    # Now iterate over the list of workshops and for each workshop check if
    # it is hosted by a portal that is accessible by the tenant.

    hosting_portals = []

    for workshop in workshop_database.get_workshops():
        if workshop.name == workshop_name:
            if (workshop.cluster, workshop.portal) in accessible_portals:
                portal = portal_database.get_portal(workshop.cluster, workshop.portal)
                if portal:
                    hosting_portals.append(portal)

    return hosting_portals


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

    cluster_database = service_state.cluster_database
    portal_database = service_state.portal_database

    if tenant_name:
        tenant = tenant_database.get_tenant_by_name(tenant_name)

        if not tenant:
            return web.Response(text="Tenant not available", status=403)

        accessible_portals = tenant.portals_which_are_accessible(
            cluster_database, portal_database
        )

    else:
        accessible_portals = set()

    # Generate the list of workshops available to the user for this tenant which
    # are in a running state. We need to eliminate any duplicates as a workshop
    # may be available through multiple training portals. We use the title and
    # description from the last found so we expect these to be consistent.

    workshop_database = service_state.workshop_database

    workshops = {}

    for workshop in currently_running_workshops(workshop_database, accessible_portals):
        workshops[workshop.name] = {
            "name": workshop.name,
            "title": workshop.title,
            "description": workshop.description,
            "labels": workshop.labels,
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
    workshop_database = service_state.workshop_database

    tenant = tenant_database.get_tenant_by_name(tenant)

    if not tenant:
        return web.Response(text="Tenant not available", status=403)

    hosting_portals = portals_hosting_workshop(
        tenant, workshop_name, workshop_database, cluster_database, portal_database
    )

    data = [
        {"name": portal.name, "cluster": portal.cluster, "url": portal.url}
        for portal in hosting_portals
    ]

    return web.json_response(data)
