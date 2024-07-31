"""Configuration database for target clusters."""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from .portals import TrainingPortal

@dataclass
class ClusterConfig:
    """Configuration object for a target cluster."""

    name: str
    uid: str
    labels: Dict[str, str]
    kubeconfig: Dict[str, Any]
    portals: Dict[str, "TrainingPortal"]

    def __init__(self, name: str, uid: str, labels: Dict[str, str], kubeconfig: Dict[str, Any]):
        self.name = name
        self.uid = uid
        self.labels = labels
        self.kubeconfig = kubeconfig
        self.portals = {}

    def add_portal(self, portal: "TrainingPortal") -> None:
        """Add a portal to the cluster."""

        self.portals[portal.name] = portal

    def remove_portal(self, name: str) -> None:
        """Remove a portal from the cluster."""

        self.portals.pop(name, None)

    def get_portals(self) -> List["TrainingPortal"]:
        """Retrieve a list of portals from the cluster."""

        return list(self.portals.values())
    
    def get_portal(self, name: str) -> "TrainingPortal":
        """Retrieve a portal from the cluster by name."""

        return self.portals.get(name)

    def get_portal_names(self) -> Dict[str, str]:
        """Retrieve a list of portal names from the cluster."""

        return {name: portal.name for name, portal in self.portals.items()}
