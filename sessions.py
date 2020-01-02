import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["session_create", "session_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "sessions")
def session_create(name, spec, logger, **_):
    return {}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "sessions")
def session_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    return {}
