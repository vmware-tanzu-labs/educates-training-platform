import logging
import itertools

import kopf

from .secretcopier_funcs import reconcile_secret as copier_reconcile_secret
from .secretinjector_funcs import reconcile_secret as injector_reconcile_secret

logger = logging.getLogger("educates")


@kopf.on.event("", "v1", "secrets")
def secret_event(
    type, event, secretcopier_index, secretexporter_index, secretinjector_index, **_
):
    obj = event["object"]
    namespace = obj["metadata"]["namespace"]
    name = obj["metadata"]["name"]

    # If secret already exists, indicated by type being None, the secret is
    # added or modified later, do a full reconcilation to ensure whether secret
    # is now a candidate for copying.

    if type not in (None, "ADDED", "MODIFIED"):
        return

    copier_configs = [
        value
        for value, *_ in itertools.chain(
            secretcopier_index.values(), secretexporter_index.values()
        )
    ]

    injector_configs = [value for value, *_ in secretinjector_index.values()]

    logger.debug(
        f"Triggering secretcopier reconcilation for secret {name} in namespace {namespace}."
    )

    copier_reconcile_secret(name, namespace, obj, copier_configs)

    logger.debug(
        f"Triggering secretinjector reconcilation for secret {name} in namespace {namespace}."
    )

    injector_reconcile_secret(name, namespace, obj, injector_configs)
