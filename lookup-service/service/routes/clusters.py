"""REST API handlers for cluster management."""

import yaml

from aiohttp import web

from .authnz import login_required, roles_accepted


@login_required
@roles_accepted("admin", "cluster-reader")
async def api_v1_clusters(request: web.Request) -> web.Response:
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
async def api_v1_clusters_details(request: web.Request) -> web.Response:
    """Returns details for the specified cluster."""

    cluster_name = request.match_info["name"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster_by_name(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    details = {
        "name": cluster.name,
        "labels": cluster.labels,
    }

    return web.json_response(details)


@login_required
@roles_accepted("admin", "cluster-reader")
async def api_v1_clusters_kubeconfig(request: web.Request) -> web.Response:
    """Returns a kubeconfig file for the specified cluster."""

    cluster_name = request.match_info["name"]

    service_state = request.app["service_state"]
    cluster_database = service_state.cluster_database

    cluster = cluster_database.get_cluster_by_name(cluster_name)

    if not cluster:
        return web.Response(text="Cluster not available", status=403)

    kubeconfig = yaml.dump(cluster.kubeconfig)

    return web.Response(text=kubeconfig)
