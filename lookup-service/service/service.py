"""Custom operator context object for the service."""

from dataclasses import dataclass

from .caches.clients import ClientDatabase
from .caches.tenants import TenantDatabase
from .caches.clusters import ClusterDatabase
from .caches.portals import PortalDatabase
from .caches.workshops import WorkshopDatabase


@dataclass
class ServiceState:
    """Custom operator context object for the service."""

    client_database: ClientDatabase
    tenant_database: TenantDatabase
    cluster_database: ClusterDatabase
    portal_database: PortalDatabase
    workshop_database: WorkshopDatabase

    def __copy__(self) -> "ServiceState":
        return self
