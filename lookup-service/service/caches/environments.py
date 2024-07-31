"""Lookup database for workshops."""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Any, Dict

from .clusters import ClusterConfig

if TYPE_CHECKING:
    from .portals import TrainingPortal


@dataclass
class WorkshopEnvironment:
    """Snapshot of workshop environment state."""

    cluster: ClusterConfig
    portal: "TrainingPortal"
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
