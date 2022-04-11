import itertools

import kopf

from .helpers import global_logger

from .secretcopier_funcs import reconcile_namespace as copier_reconcile_namespace


@kopf.on.event("", "v1", "namespaces")
def namespace_event(type, event, logger, secretcopier_index, secretexporter_index, **_):
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

    with global_logger(logger):
        copier_reconcile_namespace(name, resource, configs)
