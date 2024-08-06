"""REST API handlers for user management."""

from aiohttp import ClientSession, web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin")
async def api_get_v1_portal_user_sessions(request: web.Request) -> web.Response:
    """Returns a list of workshop sessions for a user running on portal."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]
    user_id = request.match_info["user"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    async with ClientSession() as session:
        async with portal.client_session(session) as portal_client:
            if not portal_client.connected:
                return web.Response(text="Cannot login to portal", status=503)

            data = await portal_client.user_sessions(user_id)

    return web.json_response(data)
