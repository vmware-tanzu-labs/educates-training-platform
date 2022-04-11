import itertools

import kopf

from .helpers import global_logger

from .secretinjector_funcs import (
    reconcile_service_account as injector_reconcile_service_account,
)


@kopf.on.event("", "v1", "serviceaccounts")
def serviceaccount_event(type, event, logger, secretinjector_index, **_):
    obj = event["object"]
    namespace = obj["metadata"]["namespace"]
    name = obj["metadata"]["name"]

    # If serviceaccount already exists, indicated by type being None, the
    # serviceaccount is added or modified later, do a full reconcilation to
    # ensure whether serviceaccount is now a candidate for injecting any
    # secrets.

    if type not in (None, "ADDED", "MODIFIED"):
        return

    injector_configs = [value for value, *_ in secretinjector_index.values()]

    with global_logger(logger):
        injector_reconcile_service_account(name, namespace, obj, injector_configs)
