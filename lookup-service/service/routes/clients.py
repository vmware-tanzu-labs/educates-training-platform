"""REST API handlers for client management."""

from aiohttp import web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin")
async def api_get_v1_clients(request: web.Request) -> web.Response:
    """Returns a list of clients which can access the service."""

    service_state = request.app["service_state"]
    client_database = service_state.client_database

    data = {
        "clients": [
            {"name": client.name, "roles": client.roles, "tenants": client.tenants}
            for client in client_database.get_clients()
        ]
    }

    return web.json_response(data)


@login_required
@roles_accepted("admin", "tenant")
async def api_get_v1_clients_details(request: web.Request) -> web.Response:
    """Returns details for the specified client."""

    client = request["remote_client"]
    client_roles = request["client_roles"]

    client_name = request.match_info["client"]

    if "tenant" in client_roles:
        if client.name != client_name:
            return web.Response(text="Client access not permitted", status=403)

    details = {
        "name": client.name,
        "roles": client.roles,
        "tenants": client.tenants,
    }

    return web.json_response(details)


# Set up the routes for the client management API.

routes = [
    web.get("/api/v1/clients", api_get_v1_clients),
    web.get("/api/v1/clients/{client}", api_get_v1_clients_details),
]
