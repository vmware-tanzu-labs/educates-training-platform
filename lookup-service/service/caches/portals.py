"""Configuration database for training portals."""

import logging

from dataclasses import dataclass

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from aiohttp import ClientSession, BasicAuth

from .clusters import ClusterConfig

if TYPE_CHECKING:
    from .environments import WorkshopEnvironment


logger = logging.getLogger("educates")


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

    def client_session(self, session: ClientSession) -> "TrainingPortalClientSession":
        """Create a client session for the portal."""

        return TrainingPortalClientSession(self, session)


@dataclass
class TrainingPortalClientSession:
    """Client session for a training portal."""

    portal: TrainingPortal
    session: ClientSession
    access_token: str | None

    def __init__(self, portal: TrainingPortal, session: ClientSession) -> None:
        self.portal = portal
        self.session = session
        self.access_token = None

    async def __aenter__(self) -> "TrainingPortalClientSession":
        """Login to the portal service."""

        await self.login()

        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Logout from the portal service."""

        await self.logout()

    @property
    def connected(self):
        return bool(self.access_token)

    async def login(self) -> bool:
        """Login to the portal service ."""

        async with self.session.post(
            f"{self.portal.url}/oauth2/token/",
            data={
                "grant_type": "password",
                "username": self.portal.credentials.username,
                "password": self.portal.credentials.password,
            },
            auth=BasicAuth(
                self.portal.credentials.client_id, self.portal.credentials.client_secret
            ),
        ) as response:
            if response.status != 200:
                logger.error(
                    "Failed to login to portal %s of cluster %s.",
                    self.portal.name,
                    self.portal.cluster.name,
                )

                return False

            data = await response.json()

            self.access_token = data.get("access_token")

            return True

    async def logout(self) -> None:
        """Logout from the portal service."""

        if not self.connected:
            return

        async with self.session.post(
            f"{self.portal.url}/oauth2/revoke-token/",
            data={
                "client_id": self.portal.credentials.client_id,
                "client_secret": self.portal.credentials.client_secret,
                "token": self.access_token,
            },
        ) as response:
            if response.status != 200:
                logger.error(
                    "Failed to logout from portal %s of cluster %s.",
                    self.portal.name,
                    self.portal.cluster.name,
                )

    async def user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches the list of active sessions for a user."""

        if not self.connected:
            return {}

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with self.session.get(
            f"{self.portal.url}/workshops/user/{user_id}/sessions/",
            headers=headers,
        ) as response:
            if response.status != 200:
                logger.error(
                    "Failed to get sessions from portal %s of cluster %s for user %s.",
                    self.portal.name,
                    self.portal.cluster.name,
                    user_id,
                )

                return {}

            return await response.json()
