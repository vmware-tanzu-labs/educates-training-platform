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
async def api_v1_tenants(request: web.Request) -> web.Response:
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
async def api_v1_tenants_details(request: web.Request) -> web.Response:
    """Returns details for the specified tenant."""

    tenant_name = request.match_info["name"]

    service_state = request.app["service_state"]
    tenant_database = service_state.tenant_database
    client_database = service_state.client_database

    tenant = tenant_database.get_tenant_by_name(tenant_name)

    if not tenant:
        return web.Response(text="Tenant not available", status=403)

    details = {
        "name": tenant.name,
        "clients": get_clients_mapped_to_tenant(client_database, tenant.name),
    }

    return web.json_response(details)
