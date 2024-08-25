"""HTTP API handlers and decorators for controlling access to the REST API.
"""

import datetime
from typing import Callable

import jwt
from aiohttp import web

from ..config import jwt_token_secret
from ..caches.clients import ClientConfig

TOKEN_EXPIRATION = 72  # Expiration in hours.


def generate_login_response(client: ClientConfig) -> dict:
    """Generate a JWT token for the client. The token will be set to expire and
    will need to be renewed. The token will contain the username and the unique
    identifier for the client."""

    expires_at = int(
        (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=TOKEN_EXPIRATION)
        ).timestamp()
    )

    jwt_token = jwt.encode(
        {"sub": client.name, "jti": client.identity, "exp": expires_at},
        jwt_token_secret(),
        algorithm="HS256",
    )

    return {
        "access_token": jwt_token,
        "token_type": "Bearer",
        "expires_at": expires_at,
        "roles": client.roles,
        "tenants": client.tenants,
    }


def decode_client_token(token: str) -> dict:
    """Decode the client token and return the decoded token. If the token is
    invalid, an exception will be raised."""

    return jwt.decode(token, jwt_token_secret(), algorithms=["HS256"])


@web.middleware
async def jwt_token_middleware(
    request: web.Request, handler: Callable[..., web.Response]
) -> web.Response:
    """Extract and decode the JWT token from the Authorization header, if
    present. Store the decoded details in the request object for later use by
    decorators on the individual request handlers that need to authenticate the
    client and check for required authorization.
    """

    # Extract the Authorization header from the request if present.

    authorization = request.headers.get("Authorization")

    if authorization:
        # Check if the Authorization header is a Bearer token.

        parts = authorization.split()

        if len(parts) != 2:
            return web.Response(text="Invalid Authorization header", status=400)

        if parts[0].lower() != "bearer":
            return web.Response(text="Invalid Authorization header", status=400)

        # Decode the JWT token passed in the Authorization header.

        try:
            token = parts[1]
            decoded_token = decode_client_token(token)
        except jwt.ExpiredSignatureError:
            return web.Response(text="JWT token has expired", status=401)
        except jwt.InvalidTokenError:
            return web.Response(text="JWT token is invalid", status=401)

        # Store the decoded token in the request object for later use.

        request["jwt_token"] = decoded_token
        request["client_name"] = decoded_token["sub"]

    # Continue processing the request.

    return await handler(request)


def login_required(handler: Callable[..., web.Response]) -> web.Response:
    """Decorator to verify that client is logged in to the service."""

    async def wrapper(request: web.Request) -> web.Response:
        # Check if the decoded JWT token is present in the request object.

        if "jwt_token" not in request:
            return web.Response(text="JWT token not supplied", status=400)

        decoded_token = request["jwt_token"]

        # Check the client database for the client by the name of the client
        # taken from the JWT token subject. Then check if the identity of the
        # client is still the same as the one recorded in the JWT token.

        service_state = request.app["service_state"]
        client_database = service_state.client_database

        client = client_database.get_client(decoded_token["sub"])

        if not client:
            return web.Response(text="Client details not found", status=401)

        if not client.validate_identity(decoded_token["jti"]):
            return web.Response(text="Client identity does not match", status=401)

        request["remote_client"] = client

        # Continue processing the request.

        return await handler(request)

    return wrapper


def roles_accepted(
    *roles: str,
) -> Callable[[Callable[..., web.Response]], web.Response]:
    """Decorator to check that the client has access to the endpoint by
    confirming that is has any role required by the endpoint for access."""

    def decorator(handler: Callable[..., web.Response]) -> web.Response:
        async def wrapper(request: web.Request) -> web.Response:
            # Check if the client has one of the required roles.

            client = request["remote_client"]

            matched_roles = client.has_required_role(*roles)

            if not matched_roles:
                return web.Response(text="Client access not permitted", status=403)

            request["client_roles"] = matched_roles

            # Continue processing the request.

            return await handler(request)

        return wrapper

    return decorator


async def api_auth_login(request: web.Request) -> web.Response:
    """Login handler for accessing the web application. Validates the username
    and password provided in the request and returns a JWT token if the
    credentials are valid."""

    # Extract the username and password from the request POST data.

    data = await request.json()

    username = data.get("username")
    password = data.get("password")

    if username is None:
        return web.Response(text="No username provided", status=400)

    if password is None:
        return web.Response(text="No password provided", status=400)

    # Check if the password is correct for the username.

    service_state = request.app["service_state"]
    client_database = service_state.client_database

    client = client_database.authenticate_client(username, password)

    if not client:
        return web.Response(text="Invalid username/password", status=401)

    # Generate a JWT token for the user and return it. The response is
    # bundle with the token type and expiration time so they can be used
    # by the client without needing to parse the actual JWT token.

    token = generate_login_response(client)

    return web.json_response(token)


async def api_auth_logout(request: web.Request) -> web.Response:
    """Logout handler for the web application. The client will be logged out
    and the JWT token will be invalidated."""

    # Check if the decoded JWT token is present in the request object.

    if "jwt_token" not in request:
        return web.Response(text="JWT token not supplied", status=400)

    decoded_token = request["jwt_token"]

    # Check the client database for the client by the name of the client
    # taken from the JWT token subject. Then check if the identity of the
    # client is still the same as the one recorded in the JWT token.

    service_state = request.app["service_state"]
    client_database = service_state.client_database

    client = client_database.get_client(decoded_token["sub"])

    if not client:
        return web.Response(text="Client details not found", status=401)

    if not client.validate_identity(decoded_token["jti"]):
        return web.Response(text="Client identity does not match", status=401)

    # Revoke the tokens issued to the client.

    client.revoke_tokens()

    return web.json_response({})

# Set up the middleware and routes for the authentication and authorization.

middlewares = [jwt_token_middleware]

routes = [
    web.post("/login", api_auth_login),
    web.post("/auth/login", api_auth_login),
    web.post("/auth/logout", api_auth_logout),
    web.get("/auth/verify", login_required(lambda r: web.json_response({}))),
]
