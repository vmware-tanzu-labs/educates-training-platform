"""REST API handlers for portal management."""

from aiohttp import web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin", "portal-reader")
async def api_get_v1_portals(request: web.Request) -> web.Response:
    """Returns a list of portals available to the user."""

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    portals = []

    for cluster in cluster_database.get_clusters():
        for portal in cluster.get_portals():
            portals.append(portal)

    data = {
        "portals": [
            {
                "name": portal.name,
                "uid": portal.uid,
                "generation": portal.generation,
                "labels": portal.labels,
                "cluster": portal.cluster.name,
                "url": portal.url,
                "capacity": portal.capacity,
                "allocated": portal.allocated,
                "phase": portal.phase,
            }
            for portal in portals
        ]
    }

    return web.json_response(data)


# Set up the routes for the portal management API.

routes = [web.get("/api/v1/portals", api_get_v1_portals)]
