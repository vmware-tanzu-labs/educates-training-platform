import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["session_create", "session_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "sessions")
def session_create(name, spec, logger, **_):
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # The workshop namespace needs to be the same as the workshop name.
    # The namespace created for the session is the name of the workshop
    # namespace suffixed by the user ID. By convention this should be
    # the same as what would be used for the name of the session
    # resource definition, but we can't rely on that being the case, as
    # may be different during development and testing.

    user_id = spec["userID"]
    workshop_name = spec["workshop"]

    workshop_namespace = workshop_name
    session_namespace = f"{workshop_namespace}-{user_id}"

    # Lookup the workshop resource definition and ensure it exists.

    workshop_instance = custom_objects_api.get_cluster_custom_object(
        "training.eduk8s.io", "v1alpha1", "workshops", workshop_name
    )

    # Create the primary namespace to be used for the workshop session.
    # Make the namespace for the session a child of the custom resource
    # for the session. This way the namespace will be automatically
    # deleted when the resource definition for the session is deleted
    # and we don't have to clean up anything explicitly.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": f"{session_namespace}"},
    }

    kopf.adopt(namespace_body)

    namespace_instance = core_api.create_namespace(body=namespace_body)

    # Create the service account under which the workshop session
    # instance will run. This is created in the workshop namespace. As
    # with the separate namespace, make the session custom resource the
    # parent. We will do this for all objects created for the session as
    # we go along.

    service_account = f"user-{user_id}"

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": f"{service_account}"},
    }

    kopf.adopt(service_account_body)

    service_account_instance = core_api.create_namespaced_service_account(
        namespace=workshop_namespace, body=service_account_body
    )

    # Create the rolebinding for this service account to add access to
    # the additional roles that the Kubernetes web console requires.

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {"name": f"{session_namespace}-console"},
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{workshop_namespace}-console",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "namespace": f"{workshop_namespace}",
                "name": f"{service_account}",
            }
        ],
    }

    kopf.adopt(cluster_role_binding_body)

    cluster_role_binding_instance = rbac_authorization_api.create_cluster_role_binding(
        body=cluster_role_binding_body
    )

    return {}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "sessions")
def session_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    return {}
