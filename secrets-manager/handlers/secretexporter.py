import logging
import kopf

from .secretcopier_funcs import reconcile_config

from .operator_config import OPERATOR_API_GROUP
from .helpers import lookup

logger = logging.getLogger("educates")


@kopf.index(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
def secretexporter_index(namespace, name, meta, body, **_):
    generation = meta["generation"]

    logger.debug("Add secretexporter %s with generation %s to cache.", name, generation)

    # Note that we need to add a fake `spec.sourceSecret` property to the body
    # so later rule matching works. This doesn't exist in the actual resource
    # as the resource name and namespace are used to identify the source secret.

    rules = lookup(body, "spec.rules", [])

    for rule in rules:
        rule["sourceSecret"] = {"name": name, "namespace": namespace}

    return {(namespace, name): body}


@kopf.on.resume(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
def secretexporter_reconcile_resume(name, meta, body, **_):
    generation = meta["generation"]

    logger.info("Secretexporter %s exists with generation %s.", name, generation)

    reconcile_config(name, body)


@kopf.on.create(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
@kopf.on.update(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters")
def secretexporter_reconcile_update(name, meta, body, reason, **_):
    generation = meta["generation"]

    logger.info(
        "Secretexporter %s %sd with generation %s.", name, reason.lower(), generation
    )

    reconcile_config(name, body)


@kopf.timer(
    f"secrets.{OPERATOR_API_GROUP}",
    "v1beta1",
    "secretexporters",
    initial_delay=30.0,
    interval=60.0,
)
def secretexporter_reconcile_timer(name, meta, body, **_):
    generation = meta["generation"]

    logger.debug("Reconcile secretexporter %s with generation %s.", name, generation)

    reconcile_config(name, body)


@kopf.on.delete(
    f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretexporters", optional=True
)
def secretexporter_delete(name, meta, **_):
    generation = meta["generation"]

    logger.info("Secretexporter %s with generation %s deleted.", name, generation)
