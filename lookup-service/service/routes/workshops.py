from aiohttp import web

from .access import login_required, roles_accepted


@login_required
@roles_accepted("admin")
async def api_v1_workshop_request(request: web.Request) -> web.Response:
    """Returns a workshop session for the specified tenant and workshop."""

    return web.Response(text="Workshop request")
