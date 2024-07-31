"""Configuration database for training plaform tenants."""

from dataclasses import dataclass

from typing import Any, Dict, Set

from ..helpers.selectors import ResourceSelector

from .clusters import ClusterConfig
from .portals import TrainingPortal

from .databases import PortalDatabase


@dataclass
class TenantConfig:
    """Configuration object for a tenant of the training platform."""

    name: str
    clusters: ResourceSelector
    portals: ResourceSelector

    def __init__(self, name: str, clusters: Dict[str, Any], portals: Dict[str, Any]):
        self.name = name
        self.clusters = ResourceSelector(clusters)
        self.portals = ResourceSelector(portals)

    def allowed_access_to_cluster(self, cluster: ClusterConfig) -> bool:
        """Check if the tenant has access to the cluster."""

        # Fake up a resource metadata object for the cluster.

        resource = {
            "metadata": {
                "name": cluster.name,
                "uid": cluster.uid,
                "labels": cluster.labels,
            },
        }

        return self.clusters.match_resource(resource)

    def allowed_access_to_portal(self, portal: TrainingPortal) -> bool:
        """Check if the tenant has access to the portal."""

        # Fake up a resource metadata object for the portal.

        resource = {
            "metadata": {
                "name": portal.name,
                "labels": portal.labels,
            },
        }

        return self.portals.match_resource(resource)

    def portals_which_are_accessible(
        self,
        portal_database: PortalDatabase,
    ) -> Set[str]:
        """Retrieve a list of training portals accessible by a tenant."""

        # Get the list of clusters and portals that match the tenant's rules.
        # To do this we iterate over all the portals and for each portal we then
        # check the cluster it belongs to against the tenant's cluster rules.
        # If the portal's cluster matches the tenant's cluster rules, we then
        # check the portal itself against the tenant's portal rules.

        accessible_portals = set()

        for portal in portal_database.get_portals():
            cluster = portal.cluster

            if self.allowed_access_to_cluster(cluster):
                if self.allowed_access_to_portal(portal):
                    accessible_portals.add((cluster.name, portal.name))

        return accessible_portals
