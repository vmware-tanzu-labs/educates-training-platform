"""REST API handlers for workshop requests."""

from aiohttp import web

from .authnz import login_required, roles_accepted


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
    client_database = service_state.client_database

    client_name = request["client_name"]
    client = client_database.get_client_by_name(client_name)

    if tenant_name:
        if tenant_name not in client.tenants:
            return web.Response(text="Client not allowed access to tenant", status=403)

    # Work out the set of portals accessible by the user for this tenant. The
    # tenant name may not be set if the user is an admin.

    cluster_database = service_state.cluster_database
    portal_database = service_state.portal_database

    if tenant_name:
        tenant = tenant_database.get_tenant_by_name(tenant_name)

        if not tenant:
            return web.Response(text="Tenant not available", status=403)

        accessible_portals = tenant.accessible_portals(
            cluster_database, portal_database
        )

    else:
        accessible_portals = set()

    # Generate the list of workshops available to the user for this tenant which
    # are in a running state. We need to eliminate any duplicates as a workshop
    # may be available through multiple training portals. We use the title and
    # description from the last found.

    workshop_database = service_state.workshop_database

    workshops = {}

    for workshop in workshop_database.get_workshops():
        # Make sure the workshop environment is in set of allows portals. The
        # set of accessible portals may be empty if was an admin user and no
        # tenant name was provided, in which case we allow all workshops.

        if (
            accessible_portals
            and (workshop.cluster, workshop.portal) not in accessible_portals
        ):
            continue

        # Make sure the workshop is in a running state.

        if workshop.phase != "Running":
            continue

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
    action_id = data.get("clientActionId")
    index_url = data.get("clientIndexUrl") or ""

    workshop_name = data.get("workshopName")
    parameters = data.get("workshopParams", [])

    print(
        f"Workshop request: {tenant} {user_id} {action_id} {index_url} {workshop_name} {parameters}"
    )

    return web.Response(text="Workshop request")
