"""Configuration database for clients of the service."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ClientConfiguration:
    """Configuration object for a client of the service."""

    name: str
    uid: str
    password: str
    tenants: List[str]
    roles: List[str]

    def check_password(self, password: str) -> bool:
        """Checks the password provided against the client's password."""

        return self.password == password

    def validate_identity(self, uid: str) -> bool:
        """Validate the identity provided against the client's identity."""

        return self.uid == uid

    def has_role(self, *roles: str) -> bool:
        """Check if the client has any of the roles provided."""

        return any(role in self.roles for role in roles)


@dataclass
class ClientDatabase:
    """Database for storing client configurations. Clients are stored in a
    dictionary with the client's name as the key and the client configuration
    object as the value."""

    clients: Dict[str, ClientConfiguration]

    def __init__(self):
        self.clients = {}

    def update_client(self, client: ClientConfiguration):
        """Update the client in the database. If the client does not exist in
        the database, it will be added."""

        self.clients[client.name] = client

    def remove_client(self, name: str) -> None:
        """Remove a client from the database."""

        self.clients.pop(name, None)

    def get_client_by_name(self, name: str) -> ClientConfiguration:
        """Retrieve a client from the database by name."""

        return self.clients.get(name)

    def get_client_by_uid(self, uid: str) -> ClientConfiguration:
        """Retrieve a client from the database by uid."""

        # There should only ever be one client with a given uid, so we can
        # iterate over the values of the clients dictionary and return the first
        # client that has a matching uid.

        for client in list(self.clients.values()):
            if client.validate_identity(uid):
                return client

        return None

    def get_clients_by_tenant(self, tenant: str) -> List[ClientConfiguration]:
        """Retrieves list of client from the database by tenant."""

        clients = []

        for client in list(self.clients.values()):
            if tenant in client.tenants:
                clients.append(client)

        return clients

    def authenticate_client(self, name: str, password: str) -> bool:
        """Validate a client's credentials. Returning the uid of the client if
        the credentials are valid."""

        client = self.get_client_by_name(name)

        if client is None:
            return False

        if client.check_password(password):
            return client.uid
