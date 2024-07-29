"""Lookup database for workshops."""

from dataclasses import dataclass

from typing import Dict, List, Tuple


@dataclass
class WorkshopDetails:
    """Details of a workshop."""

    name: str
    generation: int
    title: str
    description: str
    labels: Dict[str, str]
    cluster: str
    portal: str
    environment: str
    phase: str


@dataclass
class WorkshopDatabase:
    """Database for storing workshop details. Workshops are stored in a
    dictionary with the cluster, portal and workshop environment name as the key
    and the workshop details object as the value."""

    workshops: Dict[Tuple[str, str, str], WorkshopDetails]

    def __init__(self) -> None:
        self.workshops = {}

    def update_workshop(self, workshop: WorkshopDetails) -> None:
        """Update the workshop in the database. If the workshop does not exist
        in the database, it will be added."""

        key = (workshop.cluster, workshop.portal, workshop.environment)

        self.workshops[key] = workshop

    def remove_workshop(
        self, cluster_name: str, portal_name: str, environment_name: str
    ) -> None:
        """Remove a workshop from the database."""

        key = (cluster_name, portal_name, environment_name)

        self.workshops.pop(key, None)

    def get_workshops(self) -> List[WorkshopDetails]:
        """Retrieve a list of workshops from the database."""

        return list(self.workshops.values())
