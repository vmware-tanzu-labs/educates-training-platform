"""Lookup database for workshop environments."""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Dict

from wrapt import synchronized

if TYPE_CHECKING:
    from .portals import TrainingPortal
    from .sessions import WorkshopSession


@dataclass
class WorkshopEnvironment:
    """Snapshot of workshop environment state."""

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
    sessions: Dict[str, "WorkshopSession"]

    def __init__(
        self,
        portal: "TrainingPortal",
        name: str,
        generation: int,
        workshop: str,
        title: str,
        description: str,
        labels: Dict[str, str],
        capacity: int,
        reserved: int,
        allocated: int,
        available: int,
        phase: str,
    ) -> None:
        self.portal = portal
        self.name = name
        self.generation = generation
        self.workshop = workshop
        self.title = title
        self.description = description
        self.labels = labels
        self.capacity = capacity
        self.reserved = reserved
        self.allocated = allocated
        self.available = available
        self.phase = phase
        self.sessions = {}

    def get_sessions(self) -> Dict[str, "WorkshopSession"]:
        """Returns all workshop sessions."""

        return list(self.sessions.values())
    
    def get_session(self, session_name: str) -> "WorkshopSession":
        """Returns a workshop session by name."""

        return self.sessions.get(session_name)
    
    def add_session(self, session: "WorkshopSession") -> None:
        """Add a session to the environment."""

        self.sessions[session.name] = session

    def remove_session(self, session_name: str) -> None:
        """Remove a session from the environment."""

        self.sessions.pop(session_name, None)

    @synchronized
    def recalculate_capacity(self) -> None:
        """Recalculate the available capacity of the environment."""

        allocated = 0
        available = 0

        for session in list(self.sessions.values()):
            if session.phase == "Allocated":
                allocated += 1
            elif session.phase == "Available":
                available += 1

        self.allocated = allocated
        self.available = available

        print("Recalculated capacity for environment", self.name, "allocated:", allocated, "available:", available)
