"""Custom operator context object for the service."""

from dataclasses import dataclass

from .caches.databases import (
    ClientDatabase,
    TenantDatabase,
    ClusterDatabase,
    PortalDatabase,
    EnvironmentDatabase,
)


@dataclass
class ServiceState:
    """Custom operator context object for the service."""

    client_database: ClientDatabase
    tenant_database: TenantDatabase
    cluster_database: ClusterDatabase
    portal_database: PortalDatabase
    environment_database: EnvironmentDatabase

    def __copy__(self) -> "ServiceState":
        return self
