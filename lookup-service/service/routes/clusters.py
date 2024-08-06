"""REST API handlers for cluster management."""

import yaml
from aiohttp import web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin", "cluster-reader")
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
@roles_accepted("admin", "cluster-reader")
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
@roles_accepted("admin", "cluster-reader")
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
@roles_accepted("admin", "cluster-reader")
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
                "url": portal.url,
                "capacity": portal.capacity,
                "allocated": portal.allocated,
                "phase": portal.phase,
            }
            for portal in cluster.get_portals()
        ]
    }

    return web.json_response(data)


# Set up the routes for the cluster management API.

routes = [
    web.get("/api/v1/clusters", api_get_v1_clusters),
    web.get("/api/v1/clusters/{cluster}", api_get_v1_clusters_details),
    web.get("/api/v1/clusters/{cluster}/kubeconfig", api_get_v1_clusters_kubeconfig),
    web.get("/api/v1/clusters/{cluster}/portals", api_get_v1_clusters_portals),
]
