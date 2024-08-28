"""Database classes for storing state of everything."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from .clients import ClientConfig
    from .clusters import ClusterConfig
    from .tenants import TenantConfig


@dataclass
class ClientDatabase:
    """Database for storing client configurations. Clients are stored in a
    dictionary with the client's name as the key and the client configuration
    object as the value."""

    clients: Dict[str, "ClientConfig"]

    def __init__(self) -> None:
        self.clients = {}

    def update_client(self, client: "ClientConfig") -> None:
        """Update the client in the database. If the client does not exist in
        the database, it will be added."""

        self.clients[client.name] = client

    def remove_client(self, name: str) -> None:
        """Remove a client from the database."""

        self.clients.pop(name, None)

    def get_clients(self) -> List["ClientConfig"]:
        """Retrieve a list of clients from the database."""

        return list(self.clients.values())

    def get_client(self, name: str) -> "ClientConfig":
        """Retrieve a client from the database by name."""

        return self.clients.get(name)

    def authenticate_client(self, name: str, password: str) -> str | None:
        """Validate a client's credentials. Returning the the client if
        the credentials are valid."""

        client = self.get_client(name)

        if client is None:
            return

        if client.check_password(password):
            return client


@dataclass
class TenantDatabase:
    """Database for storing tenant configurations. Tenants are stored in a
    dictionary with the tenant's name as the key and the tenant configuration
    object as the value."""

    tenants: Dict[str, "TenantConfig"]

    def __init__(self):
        self.tenants = {}

    def update_tenant(self, tenant: "TenantConfig") -> None:
        """Update the tenant in the database. If the tenant does not exist in
        the database, it will be added."""

        self.tenants[tenant.name] = tenant

    def remove_tenant(self, name: str) -> None:
        """Remove a tenant from the database."""

        self.tenants.pop(name, None)

    def get_tenants(self) -> List["TenantConfig"]:
        """Retrieve a list of tenants from the database."""

        return list(self.tenants.values())

    def get_tenant(self, name: str) -> "TenantConfig":
        """Retrieve a tenant from the database by name."""

        return self.tenants.get(name)


@dataclass
class ClusterDatabase:
    """Database for storing cluster configurations. Clusters are stored in a
    dictionary with the cluster's name as the key and the cluster configuration
    object as the value."""

    clusters: Dict[str, "ClusterConfig"]

    def __init__(self) -> None:
        self.clusters = {}

    def add_cluster(self, cluster: "ClusterConfig") -> None:
        """Add the cluster to the database."""

        self.clusters[cluster.name] = cluster

    def remove_cluster(self, name: str) -> None:
        """Remove a cluster from the database."""

        self.clusters.pop(name, None)

    def get_clusters(self) -> List["ClusterConfig"]:
        """Retrieve a list of clusters from the database."""

        return list(self.clusters.values())

    def get_cluster(self, name: str) -> "ClusterConfig":
        """Retrieve a cluster from the database by name."""

        return self.clusters.get(name)


# Create the database instances.

client_database = ClientDatabase()
tenant_database = TenantDatabase()
cluster_database = ClusterDatabase()
