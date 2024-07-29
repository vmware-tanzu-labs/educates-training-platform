"""Configuration database for training portals."""

from dataclasses import dataclass

from typing import Dict, List, Tuple


@dataclass
class PortalAuth:
    """Configuration object for a portal's authentication."""

    client_id: str
    client_secret: str
    username: str
    password: str


@dataclass
class PortalState:
    """Snapshot of training portal state."""

    name: str
    uid: str
    generation: int
    labels: Dict[Tuple[str, str], str]
    cluster: str
    url: str
    capacity: int
    allocated: int
    phase: str
    auth: PortalAuth


@dataclass
class PortalDatabase:
    """Database for storing portal configurations. Portals are stored in a
    dictionary with the cluster and portal's name as the key and the portal
    configuration object as the value."""

    portals: Dict[Tuple[str, str], PortalState]

    def __init__(self) -> None:
        self.portals = {}

    def update_portal(self, portal: PortalState) -> None:
        """Update the portal in the database. If the portal does not exist in
        the database, it will be added."""

        key = (portal.cluster, portal.name)

        self.portals[key] = portal

    def remove_portal(self, cluster_name: str, portal_name: str) -> None:
        """Remove a portal from the database."""

        key = (cluster_name, portal_name)

        self.portals.pop(key, None)

    def get_portals(self) -> List[PortalState]:
        """Retrieve a list of portals from the database."""

        return list(self.portals.values())

    def get_portal(self, cluster_name: str, portal_name: str) -> PortalState:
        """Retrieve a portal from the database by cluster and name."""

        key = (cluster_name, portal_name)

        return self.portals.get(key)
