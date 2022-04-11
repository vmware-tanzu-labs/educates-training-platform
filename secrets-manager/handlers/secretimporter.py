import itertools

import kopf
import pykube

from .helpers import global_logger

from .secretcopier_funcs import reconcile_namespace

from .config import OPERATOR_API_GROUP


@kopf.on.event(f"secrets.{OPERATOR_API_GROUP}", "v1alpha1", "secretimporters")
def secretimporters_event(
    type, event, logger, secretcopier_index: kopf.Index, secretexporter_index, **_
):
    obj = event["object"]
    namespace = obj["metadata"]["namespace"]
    name = obj["metadata"]["name"]

    # If copy authorization already exists, indicated by type being
    # None, the secret is added or modified later, do a full reconcilation
    # to ensure whether secret is now a candidate for copying.

    if type not in (None, "ADDED", "MODIFIED"):
        return

    with global_logger(logger):
        # Make sure the namespace still exists before proceeding.

        api = pykube.HTTPClient(pykube.KubeConfig.from_env())

        try:
            namespace_obj = pykube.Namespace.objects(api).get(name=namespace)
        except pykube.exceptions.ObjectDoesNotExist as e:
            return

        configs = [
            value
            for value, *_ in itertools.chain(
                secretcopier_index.values(), secretexporter_index.values()
            )
        ]

        reconcile_namespace(namespace, namespace_obj.obj, configs)
