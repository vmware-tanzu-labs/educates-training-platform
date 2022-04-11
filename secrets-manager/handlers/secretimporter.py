import kopf
import pykube

from .helpers import global_logger

from .functions_copier import reconcile_namespace

from .config import OPERATOR_API_GROUP


@kopf.on.event(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretimporters")
def secretimporters_event(type, event, logger, **_):
    obj = event["object"]
    namespace = obj["metadata"]["namespace"]
    name = obj["metadata"]["name"]

    # If copy authorization already exists, indicated by type being
    # None, the secret is added or modified later, do a full reconcilation
    # to ensure whether secret is now a candidate for copying.

    with global_logger(logger):
        if type in (None, "ADDED", "MODIFIED"):
            api = pykube.HTTPClient(pykube.KubeConfig.from_env())

            try:
                namespace_obj = pykube.Namespace.objects(api).get(name=namespace)
            except pykube.exceptions.ObjectDoesNotExist as e:
                return

            reconcile_namespace(namespace, namespace_obj.obj)
