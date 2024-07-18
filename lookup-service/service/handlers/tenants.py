"""Operator handlers for tenant configuration resources."""

import logging

from typing import Any, Dict

import kopf

from ..service import ServiceState
from ..caches.tenants import TenantConfiguration
from ..helpers.objects import xgetattr

logger = logging.getLogger("educates")


@kopf.on.resume("platformtenants.platform.educates.dev")
@kopf.on.create("platformtenants.platform.educates.dev")
def platformtenants_resume(
    name: str, meta: kopf.Meta, spec: kopf.Spec, memo: ServiceState, **_
) -> Dict[str, Any]:
    """Resume the operator for the platform tenant."""

    generation = meta["generation"]

    tenant_database = memo.tenant_database

    tenant_name = name

    tenant_clusters = xgetattr(spec, "clusters", {})
    tenant_portals = xgetattr(spec, "portals", {})

    logger.info(
        "Register tenant configuration %r with generation %s.", tenant_name, generation
    )

    tenant_database.update_tenant(
        TenantConfiguration(
            name=tenant_name,
            clusters=tenant_clusters,
            portals=tenant_portals,
        )
    )

    return {}


@kopf.on.update("platformtenants.platform.educates.dev")
def platformtenants_create(
    name: str, meta: kopf.Meta, spec: kopf.Spec, memo: ServiceState, **_
) -> None:
    """Create an item for the platform tenant in the cache."""

    generation = meta["generation"]

    tenant_database = memo.tenant_database

    tenant_name = name

    tenant_clusters = xgetattr(spec, "clusters", {})
    tenant_portals = xgetattr(spec, "portals", {})

    logger.info(
        "Update tenant configuration %r with generation %s.", tenant_name, generation
    )

    tenant_database.update_tenant(
        TenantConfiguration(
            name=tenant_name,
            clusters=tenant_clusters,
            portals=tenant_portals,
        )
    )


@kopf.on.delete("platformtenants.platform.educates.dev")
def platformtenants_delete(name: str, meta: kopf.Meta, memo: ServiceState, **_) -> None:
    """Delete an item for the platform tenant in the cache."""

    generation = meta["generation"]

    tenant_database = memo.tenant_database

    tenant_name = name

    logger.info(
        "Discard tenant configuration %r with generation %s.", tenant_name, generation
    )

    tenant_database.remove_tenant(tenant_name)
