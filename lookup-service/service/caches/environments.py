"""Lookup database for workshops."""

from dataclasses import dataclass

from typing import Dict, List, Tuple

from .clusters import ClusterConfig
from .portals import PortalState


@dataclass
class EnvironmentState:
    """Snapshot of workshop environment state."""

    cluster: ClusterConfig
    portal: PortalState
    name: str
    generation: int
    workshop: str
    title: str
    description: str
    labels: Dict[str, str]
    capacity: int
    reserved: int
    allocated: int
    available: int
    phase: str


@dataclass
class EnvironmentDatabase:
    """Database for storing workshop environment details. Environments are
    stored in a dictionary with the cluster, portal and workshop environment
    name as the key and the workshop environment details object as the value."""

    environments: Dict[Tuple[str, str, str], EnvironmentState]

    def __init__(self) -> None:
        self.environments = {}

    def add_environment(self, environment: EnvironmentState) -> None:
        """Add the environment to the database."""

        key = (environment.cluster.name, environment.portal.name, environment.name)

        self.environments[key] = environment

    def remove_environment(
        self, cluster_name: str, portal_name: str, environment_name: str
    ) -> None:
        """Remove a workshop environment from the database."""

        key = (cluster_name, portal_name, environment_name)

        self.environments.pop(key, None)

    def get_environments(self) -> List[EnvironmentState]:
        """Retrieve a list of workshop environments from the database."""

        return list(self.environments.values())

    def get_environment(
        self, cluster_name: str, portal_name: str, environment_name: str
    ) -> EnvironmentState:
        """Retrieve a workshop environment from the database by cluster, portal
        and name."""

        key = (cluster_name, portal_name, environment_name)

        return self.environments.get(key)
