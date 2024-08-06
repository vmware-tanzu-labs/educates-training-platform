"""REST API handlers for tenant management."""

from aiohttp import web

from .authnz import login_required, roles_accepted


def get_clients_mapped_to_tenant(client_database, tenant_name: str) -> int:
    """Return the names of the clients mapped to the tenant."""
    return [
        client.name
        for client in client_database.get_clients()
        if tenant_name in client.tenants
    ]


@login_required
@roles_accepted("admin", "tenants-reader")
async def api_get_v1_tenants(request: web.Request) -> web.Response:
    """Returns a list of tenants."""

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database
    client_database = service_state.client_database

    data = {
        "tenants": [
            {
                "name": tenant.name,
                "clients": get_clients_mapped_to_tenant(client_database, tenant.name),
            }
            for tenant in tenant_database.get_tenants()
        ]
    }

    return web.json_response(data)


@login_required
@roles_accepted("admin", "tenants-reader")
async def api_get_v1_tenants_details(request: web.Request) -> web.Response:
    """Returns details for the specified tenant."""

    tenant_name = request.match_info["name"]

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database
    client_database = service_state.client_database

    tenant = tenant_database.get_tenant(tenant_name)

    if not tenant:
        return web.Response(text="Tenant not available", status=403)

    details = {
        "name": tenant.name,
        "clients": get_clients_mapped_to_tenant(client_database, tenant.name),
    }

    return web.json_response(details)


@login_required
@roles_accepted("admin", "tenants-reader")
async def api_get_v1_tenants_workshops(request: web.Request) -> web.Response:
    """Returns a list of workshops for the specified tenant."""

    # Grab tenant name from path parameters.

    tenant_name = request.match_info["name"]

    # Work out the set of portals accessible for this tenant.

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database

    tenant = tenant_database.get_tenant(tenant_name)

    if not tenant:
        return web.Response(text="Tenant not available", status=403)

    accessible_portals = tenant.portals_which_are_accessible()

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


# Set up the routes for the tenant management API.

routes = [
    web.get("/api/v1/tenants", api_get_v1_tenants),
    web.get("/api/v1/tenants/{name}", api_get_v1_tenants_details),
    web.get("/api/v1/tenants/{name}/workshops", api_get_v1_tenants_workshops),
]
