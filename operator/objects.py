import kubernetes.client

import wrapt

# XXX The Python swagger definitions are wrong result in creation of
# CRDs failing. For now monkey patch the Python client to fix it.


def fix_V1beta1CustomResourceDefinitionStatus___init__(wrapped, instance, args, kwargs):
    def _resolve(accepted_names=None, conditions=[], stored_versions=[]):
        return accepted_names, conditions, stored_versions

    accepted_names, conditions, stored_versions = _resolve(*args, **kwargs)

    return wrapped(
        accepted_names=accepted_names,
        conditions=conditions or [],
        stored_versions=stored_versions or [],
    )


wrapt.wrap_function_wrapper(
    "kubernetes.client.models.v1beta1_custom_resource_definition_status",
    "V1beta1CustomResourceDefinitionStatus.__init__",
    fix_V1beta1CustomResourceDefinitionStatus___init__,
)

# XXX The Python Kubernetes client doesn't currently support creating
# custom resources using its create_from_dict() function, so we need to
# do some hacks for now to get this to work for at least the eduk8s
# custom resources to support a couple of tricks. When the client is
# updated to use the dynamic API internally, then this may eventually
# work and the hacks will not be needed.
#
# Note that this doesn't solve the more general problem of being able
# to create an arbitrary custom resource.

_namespaced_crds = set(
    [
        ("WorkshopRequest", "training.eduk8s.io/v1alpha1"),
    ]
)

_cluster_crds = set(
    [
        ("Workshop", "training.eduk8s.io/v1alpha2"),
        ("WorkshopEnvironment", "training.eduk8s.io/v1alpha1"),
        ("WorkshopSession", "training.eduk8s.io/v1alpha1"),
        ("TrainingPortal", "training.eduk8s.io/v1alpha1"),
    ]
)


def create_from_dict(body):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    kind = body["kind"]
    api_version = body["apiVersion"]
    namespace = body["metadata"].get("namespace")

    annotations = body["metadata"].get("annotations", {})
    crd_scope = annotations.get("training.eduk8s.io/objects.crd.scope", "").lower()

    if crd_scope == "namespaced" or (kind, api_version) in _namespaced_crds:
        group, version = api_version.split("/")
        custom_objects_api.create_namespaced_custom_object(
            group, version, namespace, kind.lower() + "s", body
        )

    elif crd_scope == "cluster" or (kind, api_version) in _cluster_crds:
        group, version = api_version.split("/")
        custom_objects_api.create_cluster_custom_object(
            group, version, kind.lower() + "s", body
        )

    else:
        client = kubernetes.client.api_client.ApiClient()
        kubernetes.utils.create_from_dict(client, body)
