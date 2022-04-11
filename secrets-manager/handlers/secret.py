import kopf

from .helpers import global_logger

from .functions_copier import reconcile_secret as copier_reconcile_secret
from .functions_injector import reconcile_secret as injector_reconcile_secret


@kopf.on.event("", "v1", "secrets")
def secret_event(type, event, logger, **_):
    obj = event["object"]
    namespace = obj["metadata"]["namespace"]
    name = obj["metadata"]["name"]

    # If secret already exists, indicated by type being None, the
    # secret is added or modified later, do a full reconcilation to
    # ensure whether secret is now a candidate for copying.

    with global_logger(logger):
        if type in (None, "ADDED", "MODIFIED"):
            copier_reconcile_secret(name, namespace, obj)
            injector_reconcile_secret(name, namespace, obj)
