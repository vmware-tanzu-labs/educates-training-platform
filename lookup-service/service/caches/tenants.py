"""Configuration database for training plaform tenants."""

from dataclasses import dataclass

from typing import Any, Dict, List, Set

from ..helpers.selectors import ResourceSelector
from ..caches.clusters import ClusterConfiguration, ClusterDatabase
from ..caches.portals import PortalState, PortalDatabase
from .environments import EnvironmentDatabase


@dataclass
class TenantConfiguration:
    """Configuration object for a tenant of the training platform."""

    name: str
    clusters: ResourceSelector
    portals: ResourceSelector

    def __init__(self, name: str, clusters: Dict[str, Any], portals: Dict[str, Any]):
        self.name = name
        self.clusters = ResourceSelector(clusters)
        self.portals = ResourceSelector(portals)

    def allowed_access_to_cluster(self, cluster: ClusterConfiguration) -> bool:
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

    def allowed_access_to_portal(self, portal: PortalState) -> bool:
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
        cluster_database: ClusterDatabase,
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
            cluster = cluster_database.get_cluster_by_name(portal.cluster)

            if not cluster:
                continue

            if self.allowed_access_to_cluster(cluster):
                if self.allowed_access_to_portal(portal):
                    accessible_portals.add((cluster.name, portal.name))

        return accessible_portals


@dataclass
class TenantDatabase:
    """Database for storing tenant configurations. Tenants are stored in a
    dictionary with the tenant's name as the key and the tenant configuration
    object as the value."""

    tenants: Dict[str, TenantConfiguration]

    def __init__(self):
        self.tenants = {}

    def update_tenant(self, tenant: TenantConfiguration) -> None:
        """Update the tenant in the database. If the tenant does not exist in
        the database, it will be added."""

        self.tenants[tenant.name] = tenant

    def remove_tenant(self, name: str) -> None:
        """Remove a tenant from the database."""

        self.tenants.pop(name, None)

    def get_tenants(self) -> List[TenantConfiguration]:
        """Retrieve a list of tenants from the database."""

        return list(self.tenants.values())

    def get_tenant_by_name(self, name: str) -> TenantConfiguration:
        """Retrieve a tenant from the database by name."""

        return self.tenants.get(name)
