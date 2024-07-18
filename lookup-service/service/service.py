from dataclasses import dataclass

from .caches.clients import ClientDatabase
from .caches.tenants import TenantDatabase


@dataclass
class ServiceState:
    """Custom operator context object for the service."""

    client_database: ClientDatabase
    tenant_database: TenantDatabase

    def __copy__(self) -> "ServiceState":
        return self
