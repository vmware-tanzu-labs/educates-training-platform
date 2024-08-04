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

    tenant_name = data.get("tenantName")

    user_id = data.get("clientUserId") or ""
    action_id = data.get("clientActionId") or ""  # pylint: disable=unused-variable
    index_url = data.get("clientIndexUrl") or ""

    workshop_name = data.get("workshopName")
    parameters = data.get("workshopParams", [])

    if not tenant_name:
        return web.Response(text="Missing tenantName", status=400)

    if not workshop_name:
        return web.Response(text="Missing workshopName", status=400)

    # Check that client is allowed access to this tenant.

    client = request["remote_client"]

    if tenant_name not in client.tenants:
        return web.Response(text="Client not allowed access to tenant", status=403)

    # Find the portals accessible to the tenant which hosts the workshop.

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database

    tenant = tenant_database.get_tenant_by_name(tenant_name)

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
        for portal in selected_portals:
            session = portal.find_existing_workshop_session_for_user(
                user_id, workshop_name
            )

            if session:
                data = await session.reacquire_workshop_session()

                if data:
                    data["tenantName"] = tenant_name
                    return web.json_response(data)

    # For now go over the portals in turn, find the workshop environments for
    # the specified workshop that are in running state. Attempt to request a
    # new workshop session. Keep doing this until we get a successful response.

    for portal in selected_portals:
        for environment in portal.get_running_environments():
            if environment.workshop == workshop_name:
                data = await environment.request_workshop_session(
                    user_id, parameters, index_url
                )

                if data:
                    data["tenantName"] = tenant_name
                    return web.json_response(data)

    return web.Response(text="Workshop not available", status=403)
