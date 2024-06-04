import logging
import itertools

import kopf


from .secretcopier_funcs import reconcile_namespace as copier_reconcile_namespace

logger = logging.getLogger("educates")


@kopf.on.event("", "v1", "namespaces")
def namespace_event(type, event, secretcopier_index, secretexporter_index, **_):
    resource = event["object"]
    name = resource["metadata"]["name"]

    # If namespace already exists, indicated by type being None, or the
    # namespace is added or modified later, do a full reconcilation to ensure
    # that all the required secrets have been copied into the namespace.

    if type not in (None, "ADDED", "MODIFIED"):
        return

    configs = [
        value
        for value, *_ in itertools.chain(
            secretcopier_index.values(), secretexporter_index.values()
        )
    ]

    logger.debug(f"Triggering secretcopier reconcilation for namespace {name}.")

    copier_reconcile_namespace(name, resource, configs)
