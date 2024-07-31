"""Database classes for storing state of everything."""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from .clients import ClientConfig
    from .tenants import TenantConfig
    from .clusters import ClusterConfig
    from .portals import TrainingPortal
    from .environments import WorkshopEnvironment


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

    def get_client_by_name(self, name: str) -> "ClientConfig":
        """Retrieve a client from the database by name."""

        return self.clients.get(name)

    def get_client_by_uid(self, uid: str) -> "ClientConfig":
        """Retrieve a client from the database by uid."""

        # There should only ever be one client with a given uid, so we can
        # iterate over the values of the clients dictionary and return the first
        # client that has a matching uid.

        for client in list(self.clients.values()):
            if client.validate_identity(uid):
                return client

        return None

    def get_clients_by_tenant(self, tenant: str) -> List["ClientConfig"]:
        """Retrieves list of client from the database by tenant."""

        clients = []

        for client in list(self.clients.values()):
            if tenant in client.tenants:
                clients.append(client)

        return clients

    def authenticate_client(self, name: str, password: str) -> bool:
        """Validate a client's credentials. Returning the uid of the client if
        the credentials are valid."""

        client = self.get_client_by_name(name)

        if client is None:
            return False

        if client.check_password(password):
            return client.uid


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

    def get_tenant_by_name(self, name: str) -> "TenantConfig":
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

    def get_cluster_names(self) -> List[str]:
        """Retrieve a list of cluster names from the database."""

        return list(self.clusters.keys())

    def get_cluster_by_name(self, name: str) -> "ClusterConfig":
        """Retrieve a cluster from the database by name."""

        return self.clusters.get(name)


@dataclass
class PortalDatabase:
    """Database for storing portal configurations. Portals are stored in a
    dictionary with the cluster and portal's name as the key and the portal
    configuration object as the value."""

    portals: Dict[Tuple[str, str], "TrainingPortal"]

    def __init__(self) -> None:
        self.portals = {}

    def add_portal(self, portal: "TrainingPortal") -> None:
        """Add the portal to the database."""

        key = (portal.cluster.name, portal.name)

        self.portals[key] = portal

    def remove_portal(self, cluster_name: str, portal_name: str) -> None:
        """Remove a portal from the database."""

        key = (cluster_name, portal_name)

        self.portals.pop(key, None)

    def get_portals(self) -> List["TrainingPortal"]:
        """Retrieve a list of portals from the database."""

        return list(self.portals.values())

    def get_portal(self, cluster_name: str, portal_name: str) -> "TrainingPortal":
        """Retrieve a portal from the database by cluster and name."""

        key = (cluster_name, portal_name)

        return self.portals.get(key)


client_database = ClientDatabase()
tenant_database = TenantDatabase()
cluster_database = ClusterDatabase()
portal_database = PortalDatabase()
