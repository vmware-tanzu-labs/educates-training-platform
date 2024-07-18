"""Operator handlers for client configuration resources."""

import logging

from typing import Any, Dict

import kopf

from ..service import ServiceState
from ..caches.clients import ClientConfiguration
from ..helpers.objects import xgetattr

logger = logging.getLogger("educates")


@kopf.on.resume("platformclients.platform.educates.dev")
@kopf.on.create("platformclients.platform.educates.dev")
def platformclients_resume(
    name: str, meta: kopf.Meta, spec: kopf.Spec, memo: ServiceState, **_
) -> Dict[str, Any]:
    """Resume the operator for the platform client."""

    generation = meta["generation"]

    client_database = memo.client_database

    client_name = name

    client_uid = xgetattr(meta, "uid")
    client_password = xgetattr(spec, "client.password")
    client_tenants = xgetattr(spec, "tenants", [])
    client_roles = xgetattr(spec, "roles", [])

    logger.info(
        "Register client configuration %r with generation %s.", client_name, generation
    )

    client_database.update_client(
        ClientConfiguration(
            name=client_name,
            uid=client_uid,
            password=client_password,
            tenants=client_tenants,
            roles=client_roles,
        )
    )

    return {}


@kopf.on.update("platformclients.platform.educates.dev")
def platformclients_create(
    name: str, meta: kopf.Meta, spec: kopf.Spec, memo: ServiceState, **_
) -> None:
    """Create an item for the platform client in the cache."""

    generation = meta["generation"]

    client_database = memo.client_database

    client_name = name

    client_uid = xgetattr(meta, "uid")
    client_password = xgetattr(spec, "client.password")
    client_tenants = xgetattr(spec, "tenants", [])
    client_roles = xgetattr(spec, "roles", [])

    logger.info(
        "Update client configuration %r with generation %s.", client_name, generation
    )

    client_database.update_client(
        ClientConfiguration(
            name=client_name,
            uid=client_uid,
            password=client_password,
            tenants=client_tenants,
            roles=client_roles,
        )
    )


@kopf.on.delete("platformclients.platform.educates.dev")
def platformclients_delete(name: str, meta: kopf.Meta, memo: ServiceState, **_) -> None:
    """Delete an item for the platform client in the cache."""

    generation = meta["generation"]

    client_database = memo.client_database

    client_name = name

    logger.info(
        "Discard client configuration %r with generation %s.", client_name, generation
    )

    client_database.remove_client(client_name)
