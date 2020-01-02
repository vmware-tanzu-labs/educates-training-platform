import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshops")
def create(name, spec, logger, **_):
    core_api = kubernetes.client.CoreV1Api()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Use the name of the custom resource as the workshop name, and also
    # the name of the namespace created.

    workshop_name = name
    workshop_namespace = name

    # Create the namespace for everything related to this workshop.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": f"{workshop_namespace}"},
    }

    # Make the namespace for the workshop a child of the custom resource
    # for the workshop. This way the namespace will be automatically
    # deleted when the resource definition for the workshop is deleted
    # and we don't have to clean up anything explicitly.

    kopf.adopt(namespace_body)

    namespace_instance = core_api.create_namespace(body=namespace_body)

    # Because the Kubernetes web console is designed for working with
    # against whole cluster and we want to use it in scope of a single
    # namespace, we need to at least grant it roles to be able to list
    # and get namespaces. If we don't do this then the web console will
    # forever generate a stream of events complaining that it can't read
    # namespaces. This seems to hasten the web console hanging, but
    # also means can't easily switch to other namespaces the workshop
    # has access to as the list of namespaces cannot be generated. At
    # this point we therefore create a cluster role assoctaed with the
    # workshop name. This will later be bound to the service account the
    # workshop environment and web console runs as. As with the
    # namespace we add it as a child to the custom resource for the
    # workshop.

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {"name": f"{workshop_namespace}-console"},
        "rules": [
            {"apiGroups": [""], "resources": ["namespaces"], "verbs": ["get", "list"]}
        ],
    }

    kopf.adopt(cluster_role_body)

    cluster_role_instance = rbac_authorization_api.create_cluster_role(
        body=cluster_role_body
    )

    # Create any additional resources required for the workshop, as
    # defined by the workshop resource definition. Where a namespace
    # isn't defined for a namespaced resource type, the resource will be
    # created in the workshop namespace.
    #
    # XXX For now make the workshop resource definition the parent of
    # all objects. Technically should only do so for non namespaced
    # objects, or objects created in namespaces that already existed.
    # How to work out if a resource type is namespaced or not with the
    # Python Kubernetes client appears to be a bit of a hack.

    def _substitute_variables(obj):
        if isinstance(obj, str):
            obj = obj.replace("$(workshop_name)", workshop_name)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            return obj
        elif isinstance(obj, dict):
            return {k: _substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_variables(v) for v in obj]
        else:
            return obj

    if spec.get("workshop"):
        if spec["workshop"].get("objects"):
            for object_body in spec["workshop"]["objects"]:
                object_body = _substitute_variables(object_body)

                if not object_body["metadata"].get("namespace"):
                    object_body["metadata"]["namespace"] = workshop_namespace

                kopf.adopt(object_body)

                # XXX This may not be able to handle creation of custom
                # resources or any other type that the Python Kubernetes
                # client doesn't specifically know about. If that is the
                # case, will need to switch to OpenShift dynamic client
                # or see if pykube-ng client has a way of doing it.

                k8s_client = kubernetes.client.api_client.ApiClient()
                kubernetes.utils.create_from_dict(k8s_client, object_body)

    return {}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshops")
def delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    return {}
