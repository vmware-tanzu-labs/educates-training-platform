import logging

import kopf

from .secretcopier_funcs import reconcile_config

from .operator_config import OPERATOR_API_GROUP

logger = logging.getLogger("educates")


@kopf.index(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretcopiers")
def secretcopier_index(name, meta, body, **_):
    generation = meta["generation"]

    logger.debug("Add secretcopier %s with generation %s to cache.", name, generation)

    return {(None, name): body}


@kopf.on.resume(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretcopiers")
def secretcopier_reconcile_resume(name, meta, body, **_):
    generation = meta["generation"]

    logger.info("Secretcopier %s exists with generation %s.", name, generation)

    reconcile_config(name, body)


@kopf.on.create(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretcopiers")
@kopf.on.update(f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretcopiers")
def secretcopier_reconcile_update(name, meta, body, reason, **_):
    generation = meta["generation"]

    logger.info(
        "Secretcopier %s %sd with generation %s.", name, reason.lower(), generation
    )

    reconcile_config(name, body)


@kopf.timer(
    f"secrets.{OPERATOR_API_GROUP}",
    "v1beta1",
    "secretcopiers",
    initial_delay=30.0,
    interval=60.0,
)
def secretcopier_reconcile_timer(name, meta, body, **_):
    generation = meta["generation"]

    logger.debug("Reconcile secretcopier %s with generation %s.", name, generation)

    reconcile_config(name, body)


@kopf.on.delete(
    f"secrets.{OPERATOR_API_GROUP}", "v1beta1", "secretcopiers", optional=True
)
def secretcopier_delete(name, meta, **_):
    generation = meta["generation"]

    logger.info(
        "Secretcopier %s with generation %s deleted.", name, generation
    )
