"""Configuration database for training portals."""

import logging

from dataclasses import dataclass

from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

from aiohttp import ClientSession, BasicAuth

from .clusters import ClusterConfig

if TYPE_CHECKING:
    from .environments import WorkshopEnvironment
    from .sessions import WorkshopSession


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

    def recalculate_capacity(self) -> None:
        """Recalculate the capacity of the portal."""

        for environment in self.environments.values():
            environment.recalculate_capacity()

        self.allocated = sum(
            environment.allocated for environment in self.environments.values()
        )

        logger.info(
            "Recalculated capacity for portal %s: %s",
            self.name,
            {"allocated": self.allocated, "capacity": self.capacity},
        )

    def find_existing_workshop_session_for_user(
        self, user_id: str, workshop_name: str
    ) -> Union["WorkshopSession", None]:
        """Find an existing workshop session for a user."""

        for environment in self.environments.values():
            for session in environment.get_sessions():
                if (
                    session.user == user_id
                    and session.environment.workshop == workshop_name
                ):
                    return session

        return None

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

    async def reacquire_workshop_session(
        self, user_id: str, environment_name: str, session_name: str
    ) -> Dict[str, str] | None:
        """Reacquire a workshop session for a user."""

        if not self.connected:
            return

        if not session_name:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # TODO: For now index_url is still required. We provide a dummy URL
        # as what is supplied doesn't matter as a new workshop session should
        # not be created as we supply the session name.

        async with self.session.get(
            f"{self.portal.url}/workshops/environment/{environment_name}/request/",
            headers=headers,
            params={
                "index_url": "http://example.com",
                "user": user_id,
                "session": session_name,
            },
        ) as response:
            if response.status != 200:
                logger.error(
                    "Failed to reacquire session %s from portal %s of cluster %s for user %s.",
                    session_name,
                    self.portal.name,
                    self.portal.cluster.name,
                    user_id,
                )

                return

            data = await response.json()

            url = data.get("url")

            if url:
                return {
                    "clusterName": self.portal.cluster.name,
                    "portalName": self.portal.name,
                    "environmentName": environment_name,
                    "sessionName": session_name,
                    "clientUserId": user_id,
                    "sessionActionvationUrl": f"{self.portal.url}{url}"
                }

    async def request_workshop_session(
        self, environment_name: str, user_id: str, parameters: Dict[Tuple[str, str], str], index_url: str
    ) -> Dict[str, str] | None:
        """Request a workshop session for a user."""

        if not self.connected:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with self.session.get(
            f"{self.portal.url}/workshops/environment/{environment_name}/request/",
            headers=headers,
            params={
                "user": user_id,
                "parameters": parameters,
                "index_url": index_url,
            },
        ) as response:
            if response.status != 200:
                logger.error(
                    "Failed to request session from portal %s of cluster %s for user %s.",
                    self.portal.name,
                    self.portal.cluster.name,
                    user_id,
                )

                return

            data = await response.json()

            url = data.get("url")
            session_name = data.get("name")

            if url:
                return {
                    "clusterName": self.portal.cluster.name,
                    "portalName": self.portal.name,
                    "environmentName": environment_name,
                    "sessionName": session_name,
                    "clientUserId": user_id,
                    "sessionActionvationUrl": f"{self.portal.url}{url}"
                }
