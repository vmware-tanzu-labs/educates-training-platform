"""REST API handlers for cluster management."""

import yaml
from aiohttp import web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters(request: web.Request) -> web.Response:
    """Returns a list of clusters available to the user."""

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    data = {
        "clusters": [
            {"name": cluster.name, "labels": cluster.labels}
            for cluster in cluster_database.get_clusters()
        ]
    }

    return web.json_response(data)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_details(request: web.Request) -> web.Response:
    """Returns details for the specified cluster."""

    cluster_name = request.match_info["cluster"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    details = {
        "name": cluster.name,
        "labels": cluster.labels,
    }

    return web.json_response(details)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_kubeconfig(request: web.Request) -> web.Response:
    """Returns a kubeconfig file for the specified cluster."""

    cluster_name = request.match_info["cluster"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    kubeconfig = yaml.dump(cluster.kubeconfig)

    return web.Response(text=kubeconfig)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals(request: web.Request) -> web.Response:
    """Returns a list of portals for the specified cluster."""

    cluster_name = request.match_info["cluster"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

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
            for portal in cluster.get_portals()
        ]
    }

    return web.json_response(data)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals_details(request: web.Request) -> web.Response:
    """Returns details for the specified portal running on a cluster."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    details = {
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

    return web.json_response(details)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals_environments(
    request: web.Request,
) -> web.Response:
    """Returns a list of environments for a portal running on a cluster."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    environments = portal.get_environments()

    data = {
        "environments": [
            {
                "name": environment.name,
                "uid": environment.uid,
                "generation": environment.generation,
                "workshop": environment.workshop,
                "title": environment.title,
                "description": environment.description,
                "labels": environment.labels,
                "cluster": portal.cluster.name,
                "portal": portal.name,
                "capacity": environment.capacity,
                "reserved": environment.reserved,
                "allocated": environment.allocated,
                "available": environment.available,
                "phase": environment.phase,
            }
            for environment in environments
        ]
    }

    return web.json_response(data)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals_environments_details(
    request: web.Request,
) -> web.Response:
    """Returns details for the specified environment running on a portal."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]
    environment_name = request.match_info["environment"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    environment = portal.get_environment(environment_name)

    if not environment:
        return web.Response(text="Environment not available", status=403)

    details = {
        "name": environment.name,
        "uid": environment.uid,
        "generation": environment.generation,
        "workshop": environment.workshop,
        "title": environment.title,
        "description": environment.description,
        "labels": environment.labels,
        "cluster": portal.cluster.name,
        "portal": portal.name,
        "capacity": environment.capacity,
        "reserved": environment.reserved,
        "allocated": environment.allocated,
        "available": environment.available,
        "phase": environment.phase,
    }

    return web.json_response(details)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals_environments_sessions(
    request: web.Request,
) -> web.Response:
    """Returns a list of workshop sessions for an environment running on portal."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]
    environment_name = request.match_info["environment"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    environment = portal.get_environment(environment_name)

    if not environment:
        return web.Response(text="Environment not available", status=403)

    sessions = environment.get_sessions()

    data = {
        "sessions": [
            {
                "name": session.name,
                "generation": session.generation,
                "cluster": session.environment.portal.cluster.name,
                "portal": session.environment.portal.name,
                "environment": session.environment.name,
                "workshop": session.environment.workshop,
                "phase": session.phase,
                "user": session.user,
            }
            for session in sessions
        ]
    }

    return web.json_response(data)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals_environments_users(
    request: web.Request,
) -> web.Response:
    """Returns a list of users for an environment running on portal."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]
    environment_name = request.match_info["environment"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    environment = portal.get_environment(environment_name)

    if not environment:
        return web.Response(text="Environment not available", status=403)

    sessions = environment.get_sessions()

    users = set()

    for session in sessions:
        if session.user not in users:
            users.add(session.user)

    data = {"users": list(users)}

    return web.json_response(data)


@login_required
@roles_accepted("admin")
async def api_get_v1_clusters_portals_environments_users_sessions(
    request: web.Request,
) -> web.Response:
    """Returns a list of workshop sessions for a user in an environment running on portal."""

    cluster_name = request.match_info["cluster"]
    portal_name = request.match_info["portal"]
    environment_name = request.match_info["environment"]
    user_name = request.match_info["user"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    portal = cluster.get_portal(portal_name)

    if not portal:
        return web.Response(text="Portal not available", status=403)

    environment = portal.get_environment(environment_name)

    if not environment:
        return web.Response(text="Environment not available", status=403)

    sessions = environment.get_sessions()

    data = {
        "sessions": [
            {
                "name": session.name,
                "generation": session.generation,
                "cluster": session.environment.portal.cluster.name,
                "portal": session.environment.portal.name,
                "environment": session.environment.name,
                "workshop": session.environment.workshop,
                "phase": session.phase,
                "user": session.user,
            }
            for session in sessions
            if session.user == user_name
        ]
    }

    return web.json_response(data)


# Set up the routes for the cluster management API.

routes = [
    web.get("/api/v1/clusters", api_get_v1_clusters),
    web.get("/api/v1/clusters/{cluster}", api_get_v1_clusters_details),
    web.get("/api/v1/clusters/{cluster}/kubeconfig", api_get_v1_clusters_kubeconfig),
    web.get("/api/v1/clusters/{cluster}/portals", api_get_v1_clusters_portals),
    web.get(
        "/api/v1/clusters/{cluster}/portals/{portal}",
        api_get_v1_clusters_portals_details,
    ),
    web.get(
        "/api/v1/clusters/{cluster}/portals/{portal}/environments",
        api_get_v1_clusters_portals_environments,
    ),
    web.get(
        "/api/v1/clusters/{cluster}/portals/{portal}/environments/{environment}",
        api_get_v1_clusters_portals_environments_details,
    ),
    web.get(
        "/api/v1/clusters/{cluster}/portals/{portal}/environments/{environment}/sessions",
        api_get_v1_clusters_portals_environments_sessions,
    ),
    web.get(
        "/api/v1/clusters/{cluster}/portals/{portal}/environments/{environment}/users",
        api_get_v1_clusters_portals_environments_users,
    ),
    web.get(
        "/api/v1/clusters/{cluster}/portals/{portal}/environments/{environment}/users/{user}/sessions",  # pylint: disable=line-too-long
        api_get_v1_clusters_portals_environments_users_sessions,
    ),
]
