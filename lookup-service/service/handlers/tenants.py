"""Operator handlers for tenant configuration resources."""

import logging
from typing import Any, Dict

import kopf

from ..caches.tenants import TenantConfig
from ..helpers.objects import xgetattr
from ..service import ServiceState

logger = logging.getLogger("educates")


@kopf.on.resume("tenantconfigs.lookup.educates.dev")
@kopf.on.create("tenantconfigs.lookup.educates.dev")
@kopf.on.update("tenantconfigs.lookup.educates.dev")
def tenantconfigs_update(
    name: str, meta: kopf.Meta, spec: kopf.Spec, memo: ServiceState, reason: str, **_
) -> Dict[str, Any]:
    """Add the tenant configuration to the tenant database."""

    generation = meta["generation"]

    tenant_name = name

    tenant_clusters = xgetattr(spec, "clusters", {})
    tenant_portals = xgetattr(spec, "portals", {})

    logger.info(
        "%s tenant configuration %r with generation %s.",
        (reason == "update") and "Update" or "Register",
        name,
        generation,
    )

    tenant_database = memo.tenant_database

    tenant_database.update_tenant(
        TenantConfig(
            name=tenant_name,
            clusters=tenant_clusters,
            portals=tenant_portals,
        )
    )

    return {}


@kopf.on.delete("tenantconfigs.lookup.educates.dev")
def tenantconfigs_delete(name: str, meta: kopf.Meta, memo: ServiceState, **_) -> None:
    """Remove the tenant configuration from the tenant database."""

    generation = meta["generation"]

    tenant_database = memo.tenant_database

    tenant_name = name

    logger.info(
        "Discard tenant configuration %r with generation %s.", tenant_name, generation
    )

    tenant_database.remove_tenant(tenant_name)
