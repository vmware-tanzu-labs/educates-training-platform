"""Model objects for workshop sessions."""

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .environments import WorkshopEnvironment

@dataclass
class WorkshopSession:
    """Snapshot of workshop session state."""

    environment: "WorkshopEnvironment"
    name: str
    generation: int
    phase: str
    user: str
