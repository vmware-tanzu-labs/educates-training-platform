"""Configuration database for target clusters."""

from dataclasses import dataclass

from typing import Any, Dict


@dataclass
class ClusterConfig:
    """Configuration object for a target cluster."""

    name: str
    uid: str
    labels: Dict[str, str]
    kubeconfig: Dict[str, Any]
