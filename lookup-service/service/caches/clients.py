"""Configuration database for clients of the service."""

from dataclasses import dataclass

from typing import List, Set


@dataclass
class ClientConfig:
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

    def has_any_role(self, *roles: str) -> Set:
        """Check if the client has any of the roles provided. We provided
        back a set containing the roles that matched."""

        matched_roles = set()

        for role in roles:
            if role in self.roles:
                matched_roles.add(role)

        return matched_roles
