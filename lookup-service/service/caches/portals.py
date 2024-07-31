"""Configuration database for training portals."""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Dict, List, Tuple

from .databases import environment_database

from .clusters import ClusterConfig

if TYPE_CHECKING:
    from .environments import WorkshopEnvironment


@dataclass
class PortalCredentials:
    """Configuration object for a portal's authentication."""

    client_id: str
    client_secret: str
    username: str
    password: str


@dataclass
class TrainingPortal:
    """Snapshot of training portal state."""

    cluster: ClusterConfig
    name: str
    uid: str
    generation: int
    labels: Dict[Tuple[str, str], str]
    url: str
    capacity: int
    allocated: int
    phase: str
    credentials: PortalCredentials

    @property
    def environments(
        self,
    ) -> List["WorkshopEnvironment"]:
        """Return the workshop environments associated with this portal."""

        return [
            environment
            for environment in environment_database.get_environments()
            if environment.cluster.name == self.cluster.name
            and environment.portal.name == self.name
        ]
