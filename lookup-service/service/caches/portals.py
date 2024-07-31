"""Configuration database for training portals."""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Dict, List, Tuple

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
    credentials: PortalCredentials
    phase: str
    capacity: int
    allocated: int
    environments: Dict[str, "WorkshopEnvironment"]

    def __init__(
        self,
        cluster: ClusterConfig,
        name: str,
        uid: str,
        generation: int,
        labels: Dict[str, str],
        url: str,
        credentials: PortalCredentials,
        phase: str,
        capacity: int,
        allocated: int,
    ) -> None:
        self.cluster = cluster
        self.name = name
        self.uid = uid
        self.generation = generation
        self.labels = labels
        self.url = url
        self.credentials = credentials
        self.phase = phase
        self.capacity = capacity
        self.allocated = allocated
        self.environments = {}

    def get_environments(self) -> List["WorkshopEnvironment"]:
        """Returns all workshop environments."""

        return list(self.environments.values())

    def get_running_environments(self) -> List["WorkshopEnvironment"]:
        """Returns all running workshop environments."""

        return [
            environment
            for environment in self.environments.values()
            if environment.phase == "Running"
        ]

    def get_environment(self, environment_name: str) -> "WorkshopEnvironment":
        """Returns a workshop environment by name."""

        return self.environments.get(environment_name)

    def add_environment(self, environment: "WorkshopEnvironment") -> None:
        """Add a workshop environment to the portal."""

        self.environments[environment.name] = environment

    def remove_environment(self, environment_name: str) -> None:
        """Remove a workshop environment from the portal."""

        self.environments.pop(environment_name, None)

    def hosts_workshop(self, workshop_name: str) -> bool:
        """Check if the portal hosts a workshop."""

        for environment in self.environments.values():
            if environment.workshop == workshop_name:
                return True
            
        return False
