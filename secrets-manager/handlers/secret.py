import itertools

import kopf

from .helpers import global_logger

from .secretcopier_funcs import reconcile_secret as copier_reconcile_secret
from .secretinjector_funcs import reconcile_secret as injector_reconcile_secret


@kopf.on.event("", "v1", "secrets")
def secret_event(
    type,
    event,
    logger,
    secretcopier_index,
    secretexporter_index,
    secretinjector_index,
    **_
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

    with global_logger(logger):
        copier_reconcile_secret(name, namespace, obj, copier_configs)
        injector_reconcile_secret(name, namespace, obj, injector_configs)
