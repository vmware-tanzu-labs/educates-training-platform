"""Handlers for HTTP API endpoints."""

from aiohttp import web

from . import authnz, clients, clusters, portals, tenants, users, workshops


def register_routes(app: web.Application) -> None:
    """Register the HTTP API routes with the application."""

    # Register authentication and authorization middleware/routes.

    app.middlewares.extend(authnz.middlewares)
    app.add_routes(authnz.routes)

    # Register the routes for the different parts of the service.

    app.add_routes(clients.routes)
    app.add_routes(clusters.routes)
    app.add_routes(portals.routes)
    app.add_routes(tenants.routes)
    app.add_routes(users.routes)
    app.add_routes(workshops.routes)
