"""Configuration database for training plaform tenants."""

from dataclasses import dataclass

from typing import Any, Dict, List

from ..helpers.selectors import ResourceSelector


@dataclass
class TenantConfiguration:
    """Configuration object for a tenant of the training platform."""

    name: str
    clusters: List[ResourceSelector]
    portals: List[ResourceSelector]

    def __init__(self, name: str, clusters: Dict[str, Any], portals: Dict[str, Any]):
        self.name = name
        self.clusters = ResourceSelector(clusters)
        self.portals = ResourceSelector(portals)


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

    def get_tenant_by_name(self, name: str) -> TenantConfiguration:
        """Retrieve a tenant from the database by name."""

        return self.tenants.get(name)
