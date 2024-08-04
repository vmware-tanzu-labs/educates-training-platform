"""Model objects for workshop sessions."""

from dataclasses import dataclass

from aiohttp import ClientSession

from typing import TYPE_CHECKING, Dict

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

    async def reacquire_workshop_session(self) -> Dict[str, str] | None:
        """Returns the activation URL. This entails needing to make a REST API
        request to the training portal to get the activation URL."""

        portal = self.environment.portal

        async with ClientSession() as http_client:
            async with portal.client_session(http_client) as portal_client:
                if not portal_client.connected:
                    return

                return await portal_client.reacquire_workshop_session(
                    self.user,
                    environment_name=self.environment.name,
                    session_name=self.name,
                )