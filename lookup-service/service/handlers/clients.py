"""Operator handlers for client configuration resources."""

import logging

from typing import Any, Dict

import kopf

from ..service import ServiceState
from ..caches.clients import ClientConfig
from ..helpers.objects import xgetattr

logger = logging.getLogger("educates")


@kopf.on.resume("clientconfigs.lookup.educates.dev")
@kopf.on.create("clientconfigs.lookup.educates.dev")
@kopf.on.update("clientconfigs.lookup.educates.dev")
def clientconfigs_update(
    name: str, meta: kopf.Meta, spec: kopf.Spec, memo: ServiceState, reason: str, **_
) -> Dict[str, Any]:
    """Add the client configuration to the client database."""

    generation = meta["generation"]

    client_name = name

    client_uid = xgetattr(meta, "uid")
    client_password = xgetattr(spec, "client.password")
    client_tenants = xgetattr(spec, "tenants", [])
    client_roles = xgetattr(spec, "roles", [])

    logger.info(
        "%s client configuration %r with generation %s.",
        (reason == "update") and "Update" or "Register",
        name,
        generation,
    )

    client_database = memo.client_database

    client_database.update_client(
        ClientConfig(
            name=client_name,
            uid=client_uid,
            password=client_password,
            tenants=client_tenants,
            roles=client_roles,
        )
    )

    return {}


@kopf.on.delete("clientconfigs.lookup.educates.dev")
def clientconfigs_delete(name: str, meta: kopf.Meta, memo: ServiceState, **_) -> None:
    """Remove the client configuration from the client database."""

    generation = meta["generation"]

    client_database = memo.client_database

    client_name = name

    logger.info(
        "Discard client configuration %r with generation %s.", client_name, generation
    )

    client_database.remove_client(client_name)
