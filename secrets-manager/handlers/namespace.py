import kopf

from .helpers import global_logger

from .functions_copier import reconcile_namespace as copier_reconcile_namespace


@kopf.on.event("", "v1", "namespaces")
def namespace_event(type, event, logger, **_):
    resource = event["object"]
    name = resource["metadata"]["name"]

    # If namespace already exists, indicated by type being None, or the
    # namespace is added or modified later, do a full reconcilation to
    # ensure that all the required secrets have been copied into the
    # namespace.

    with global_logger(logger):
        if type in (None, "ADDED", "MODIFIED"):
            copier_reconcile_namespace(name, resource)
