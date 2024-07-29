"""REST API handlers for portal management."""

import yaml

from aiohttp import web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin", "portal-reader")
async def api_v1_portals(request: web.Request) -> web.Response:
    """Returns a list of portals available to the user."""

    service_state = request.app["service_state"]
    portal_database = service_state.portal_database

    data = {
        "portals": [
            {
                "name": portal.name,
                "uid": portal.uid,
                "generation": portal.generation,
                "labels": portal.labels,
                "cluster": portal.cluster,
                "url": portal.url,
                "phase": portal.phase,
            }
            for portal in portal_database.get_portals()
        ]
    }

    return web.json_response(data)
