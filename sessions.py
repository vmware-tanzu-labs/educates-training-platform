import random

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["session_create", "session_delete"]


_resource_budgets = {
    "small": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "1", "memory": "1Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "1", "memory": "1Gi"},
                        "default": {"cpu": "250m", "memory": "256Mi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "1Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "hard": {"limits.cpu": "1", "limits.memory": "1Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "hard": {"limits.cpu": "1", "limits.memory": "1Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "3",
                    "replicationcontrollers": "10",
                    "secrets": "20",
                    "services": "5",
                }
            },
        },
    },
    "medium": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "2", "memory": "2Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "2", "memory": "2Gi"},
                        "default": {"cpu": "500m", "memory": "512Mi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "5Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "hard": {"limits.cpu": "2", "limits.memory": "2Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "hard": {"limits.cpu": "2", "limits.memory": "2Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "6",
                    "replicationcontrollers": "15",
                    "secrets": "25",
                    "services": "10",
                }
            },
        },
    },
    "large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "4", "memory": "4Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "4", "memory": "4Gi"},
                        "default": {"cpu": "500m", "memory": "1Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "10Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "hard": {"limits.cpu": "4", "limits.memory": "4Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "hard": {"limits.cpu": "4", "limits.memory": "4Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "12",
                    "replicationcontrollers": "25",
                    "secrets": "35",
                    "services": "20",
                }
            },
        },
    },
    "x-large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "8", "memory": "8Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "8", "memory": "8Gi"},
                        "default": {"cpu": "500m", "memory": "2Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "20Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "8", "limits.memory": "8Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "8", "limits.memory": "8Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "18",
                    "replicationcontrollers": "35",
                    "secrets": "45",
                    "services": "30",
                }
            },
        },
    },
    "xx-large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "12", "memory": "12Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "12", "memory": "12Gi"},
                        "default": {"cpu": "500m", "memory": "2Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "20Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "12", "limits.memory": "12Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "12", "limits.memory": "12Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "24",
                    "replicationcontrollers": "45",
                    "secrets": "55",
                    "services": "40",
                }
            },
        },
    },
    "xxx-large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "16", "memory": "16Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "16", "memory": "16Gi"},
                        "default": {"cpu": "500m", "memory": "2Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "20Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "16", "limits.memory": "16Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "16", "limits.memory": "16Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "30",
                    "replicationcontrollers": "55",
                    "secrets": "65",
                    "services": "50",
                }
            },
        },
    },
}


def _setup_limits_and_quotas(
    workshop_namespace, target_namespace, service_account, role, budget
):
    core_api = kubernetes.client.CoreV1Api()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Create role binding in the namespace so the service account under
    # which the workshop environment runs can create resources in it.

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {"name": "eduk8s"},
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{role}",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": f"{service_account}",
                "namespace": f"{workshop_namespace}",
            }
        ],
    }

    rbac_authorization_api.create_namespaced_role_binding(
        namespace=target_namespace, body=role_binding_body
    )

    # Determine which limit ranges and resources quotas to be used.

    if budget != "custom":
        if budget not in _resource_budgets:
            budget = "default"
        elif not _resource_budgets[budget]:
            budget = "default"

    if budget not in ("default", "custom"):
        budget_item = _resource_budgets[budget]

        resource_limits_definition = budget_item["resource-limits"]
        compute_resources_definition = budget_item["compute-resources"]
        compute_resources_timebound_definition = budget_item[
            "compute-resources-timebound"
        ]
        object_counts_definition = budget_item["object-counts"]

    # Delete any limit ranges applied to the namespace that may conflict
    # with the limit range being applied. For the case of custom, we
    # delete any being applied but don't replace it. It is assumed that
    # the session objects for the workshop will define any limit ranges
    # and resource quotas itself.

    if budget != "default":
        limit_ranges = core_api.list_namespaced_limit_range(namespace=target_namespace)

        for limit_range in limit_ranges.items:
            core_api.delete_namespaced_limit_range(
                namespace=target_namespace, name=limit_range["metadata"]["name"]
            )

    # Create limit ranges for the namespace so any deployments will have
    # default memory/cpu min and max values.

    if budget not in ("default", "custom"):
        resource_limits_body = resource_limits_definition
        core_api.create_namespaced_limit_range(
            namespace=target_namespace, body=resource_limits_body
        )

    # Delete any resource quotas applied to the namespace that may
    # conflict with the resource quotas being applied.

    if budget != "default":
        resource_quotas = core_api.list_namespaced_resource_quota(
            namespace=target_namespace
        )

        for resource_quota in resource_quotas.items:
            core_api.delete_namespaced_resource_quota(
                namespace=target_namespace, name=resource_quota["metadata"]["name"]
            )

    # Create resource quotas for the namespace so there is a maximum for
    # what resources can be used.

    if budget not in ("default", "custom"):
        resource_quota_body = compute_resources_definition
        core_api.create_namespaced_resource_quota(
            namespace=target_namespace, body=resource_quota_body
        )

        resource_quota_body = compute_resources_timebound_definition
        core_api.create_namespaced_resource_quota(
            namespace=target_namespace, body=resource_quota_body
        )

        resource_quota_body = object_counts_definition
        core_api.create_namespaced_resource_quota(
            namespace=target_namespace, body=resource_quota_body
        )


@kopf.on.create("training.eduk8s.io", "v1alpha1", "sessions")
def session_create(name, spec, logger, **_):
    apps_api = kubernetes.client.AppsV1Api()
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    extensions_api = kubernetes.client.ExtensionsV1beta1Api()
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

    session_name = name

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

    core_api.create_namespace(body=namespace_body)

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

    core_api.create_namespaced_service_account(
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

    rbac_authorization_api.create_cluster_role_binding(body=cluster_role_binding_body)

    # Setup limit ranges and projects quotas on the primary session namespace.

    role = "admin"
    budget = "default"

    if workshop_instance["spec"].get("session"):
        role = workshop_instance["spec"]["session"].get("role", role)
        budget = workshop_instance["spec"]["session"].get("budget", budget)

    _setup_limits_and_quotas(
        workshop_namespace, session_namespace, service_account, role, budget,
    )

    # Create any additional resource objects required for the session.
    #
    # XXX For now make the session resource definition the parent of
    # all objects. Technically should only do so for non namespaced
    # objects, or objects created in namespaces that already existed.
    # How to work out if a resource type is namespaced or not with the
    # Python Kubernetes client appears to be a bit of a hack.

    def _substitute_variables(obj):
        if isinstance(obj, str):
            obj = obj.replace("$(user_id)", user_id)
            obj = obj.replace("$(session_name)", session_name)
            obj = obj.replace("$(session_namespace)", session_namespace)
            obj = obj.replace("$(service_account)", service_account)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            return obj
        elif isinstance(obj, dict):
            return {k: _substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_variables(v) for v in obj]
        else:
            return obj

    objects = []

    if workshop_instance["spec"].get("session"):
        objects = workshop_instance["spec"]["session"].get("objects", [])

    for object_body in objects:
        kind = object_body["kind"]
        api_version = object_body["apiVersion"]

        object_body = _substitute_variables(object_body)

        if not object_body["metadata"].get("namespace"):
            object_body["metadata"]["namespace"] = session_namespace

        kopf.adopt(object_body)

        # XXX This may not be able to handle creation of custom
        # resources or any other type that the Python Kubernetes client
        # doesn't specifically know about. If that is the case, will
        # need to switch to OpenShift dynamic client or see if pykube-ng
        # client has a way of doing it.

        k8s_client = kubernetes.client.api_client.ApiClient()
        kubernetes.utils.create_from_dict(k8s_client, object_body)

        if api_version == "v1" and kind.lower() == "namespace":
            annotations = object_body["metadata"].get("annotations", {})

            target_role = annotations.get("session/role", role)
            target_budget = annotations.get("session/budget", budget)

            secondary_namespace = object_body["metadata"]["name"]

            _setup_limits_and_quotas(
                workshop_namespace,
                secondary_namespace,
                service_account,
                target_role,
                target_budget,
            )

    # Deploy the workshop dashboard environment for the session. First
    # create a secret for the Kubernetes web console that must exist
    # otherwise it will not even start up.

    secret_body = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "kubernetes-dashboard-csrf"},
    }

    core_api.create_namespaced_secret(namespace=session_namespace, body=secret_body)

    # Next setup the deployment resource for the workshop dashboard.

    username = spec.get("username", "")
    password = spec.get("password", "")

    image = workshop_instance["spec"]["image"]

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": f"workshop-{user_id}"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": f"workshop-{user_id}"}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {"labels": {"deployment": f"workshop-{user_id}"}},
                "spec": {
                    "serviceAccountName": f"{service_account}",
                    "containers": [
                        {
                            "name": "workshop",
                            "image": f"{image}",
                            "imagePullPolicy": "Always",
                            "ports": [{"containerPort": 10080, "protocol": "TCP"}],
                            "env": [
                                {
                                    "name": "SESSION_NAMESPACE",
                                    "value": f"{session_namespace}",
                                },
                                {"name": "AUTH_USERNAME", "value": f"{username}",},
                                {"name": "AUTH_PASSWORD", "value": f"{password}",},
                            ],
                        }
                    ],
                },
            },
        },
    }

    # Apply any patches for the pod specification for the deployment which
    # are specified in the workshop resource definition. This would be used
    # to set resources and setup volumes.

    deployment_patch = {}

    if workshop_instance["spec"].get("session"):
        deployment_patch = workshop_instance["spec"]["session"].get("patches", {})

    def _smart_overlay_merge(target, patch):
        if isinstance(patch, dict):
            for key, value in patch.items():
                if key not in target:
                    target[key] = value
                elif type(target[key]) != type(value):
                    target[key] = value
                elif isinstance(value, (dict, list)):
                    _smart_overlay_merge(target[key], value)
                else:
                    target[key] = value
        elif isinstance(patch, list):
            for patch_item in patch:
                if isinstance(patch_item, dict) and "name" in patch_item:
                    for i, target_item in enumerate(target):
                        if (
                            isinstance(target_item, dict)
                            and target_item.get("name") == patch_item["name"]
                        ):
                            _smart_overlay_merge(target[i], patch_item)
                            break
                    else:
                        target.append(patch_item)
                else:
                    target.append(patch_item)

    if deployment_patch:
        deployment_patch = _substitute_variables(deployment_patch)

        _smart_overlay_merge(deployment_body["spec"]["template"], deployment_patch)

    # Apply any environment variable overrides for the workshop environment.

    environment_patch = spec.get("env", [])

    if environment_patch:
        if (
            deployment_body["spec"]["template"]["spec"]["containers"][0].get("env")
            is None
        ):
            deployment_body["spec"]["template"]["spec"]["containers"][0][
                "env"
            ] = environment_patch
        else:
            _smart_overlay_merge(
                deployment_body["spec"]["template"]["spec"]["containers"][0]["env"],
                environment_patch,
            )

    # Finally create the deployment for the workshop environment.

    kopf.adopt(deployment_body)

    apps_api.create_namespaced_deployment(
        namespace=workshop_namespace, body=deployment_body
    )

    # Create a service so that the workshop environment can be accessed.
    # This is only internal to the cluster, so port forwarding or an
    # ingress is still needed to access it from outside of the cluster.

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": f"workshop-{user_id}"},
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 10080, "protocol": "TCP", "targetPort": 10080}],
            "selector": {"deployment": f"workshop-{user_id}"},
        },
    }

    kopf.adopt(service_body)

    core_api.create_namespaced_service(namespace=workshop_namespace, body=service_body)

    # If a hostname or a domain is defined, create an ingress to access
    # the workshop environment. In the case of only the domain being
    # provided, the session name becomes the host subdomain.
    #
    # XXX No support for using a secure connection at this point.

    hostname = spec.get("hostname", "")
    domain = spec.get("domain", "")

    if not hostname and domain:
        hostname = f"{session_name}.{domain}"

    if hostname:
        ingress_body = {
            "apiVersion": "extensions/v1beta1",
            "kind": "Ingress",
            "metadata": {"name": f"workshop-{user_id}"},
            "spec": {
                "rules": [
                    {
                        "host": f"{hostname}",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "backend": {
                                        "serviceName": f"workshop-{user_id}",
                                        "servicePort": 10080,
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
        }

        kopf.adopt(ingress_body)

        extensions_api.create_namespaced_ingress(
            namespace=workshop_namespace, body=ingress_body
        )

    return {}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "sessions")
def session_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    return {}
