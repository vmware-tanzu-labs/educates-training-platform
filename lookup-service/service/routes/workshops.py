"""REST API handlers for workshop requests."""

from aiohttp import web

from .access import login_required, roles_accepted


@login_required
@roles_accepted("admin")
async def api_v1_workshop_request(request: web.Request) -> web.Response:
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
