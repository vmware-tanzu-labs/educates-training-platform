import os
import time
import random
import string
import base64
import json

import bcrypt

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

from system_profile import (
    operator_ingress_domain,
    operator_ingress_secret,
    operator_ingress_class,
    environment_image_pull_secrets,
)
from objects import create_from_dict

__all__ = ["workshop_session_create", "workshop_session_delete"]


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
            "name": role,
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": service_account,
                "namespace": workshop_namespace,
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

        # Verify that the status of the resource quotas have been
        # updated. If we don't do this, then the calculated hard limits
        # may not be calculated before we start creating resources in
        # the namespace resulting in a failure. If we can't manage to
        # verify quotas after a period of, give up. This may result in a
        # subsequent failure.

        for _ in range(25):
            resource_quotas = core_api.list_namespaced_resource_quota(
                namespace=target_namespace
            )

            if not resource_quotas.items:
                break

            for resource_quota in resource_quotas.items:
                if not resource_quota.status or not resource_quota.status.hard:
                    time.sleep(0.1)
                    continue

            break


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshopsessions", id="eduk8s")
def workshop_session_create(name, spec, logger, **_):
    apps_api = kubernetes.client.AppsV1Api()
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    extensions_api = kubernetes.client.ExtensionsV1beta1Api()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # The namespace created for the session is the name of the workshop
    # namespace suffixed by the session ID. By convention this should be
    # the same as what would be used for the name of the session
    # resource definition, but we can't rely on that being the case, as
    # may be different during development and testing, so we construct
    # the name ourself.

    environment_name = spec["environment"]["name"]
    workshop_namespace = environment_name

    try:
        environment_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopenvironments", workshop_namespace
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise kopf.TemporaryError("Namespace doesn't correspond to workshop.")

    session_id = spec["session"]["id"]
    session_namespace = f"{workshop_namespace}-{session_id}"

    # We pull details of the workshop to be deployed from the status of
    # the workspace custom resource. This is a copy of the specification
    # from the custom resource for the workshop. We use a copy so we
    # aren't affected by changes in the original workshop made after the
    # workspace was created.

    if not environment_instance.get("status") or not environment_instance["status"].get(
        "eduk8s"
    ):
        raise kopf.TemporaryError("Environment for workshop not ready.")

    workshop_spec = environment_instance["status"]["eduk8s"]["workshop"]["spec"]

    # Calculate the hostname and domain being used. Need to do this so
    # we can later set the INGRESS_DOMAIN environment variable on the
    # deployment so that it is available in the workshop environment,
    # but also so we can use it replace variables in list of resource
    # objects being created.

    ingress_protocol = "http"

    system_profile = spec.get("system", {}).get("profile")

    default_ingress_domain = operator_ingress_domain(system_profile)
    default_ingress_secret = operator_ingress_secret(system_profile)
    default_ingress_class = operator_ingress_class(system_profile)

    ingress_domain = (
        spec["session"].get("ingress", {}).get("domain", default_ingress_domain)
    )

    ingress_class = (
        spec["session"].get("ingress", {}).get("class", default_ingress_class)
    )

    session_hostname = f"{session_namespace}.{ingress_domain}"

    if ingress_domain == default_ingress_domain:
        ingress_secret = default_ingress_secret
    else:
        ingress_secret = spec["session"].get("ingress", {}).get("secret", "")

    # If a TLS secret is specified, ensure that the secret exists in the
    # workshop namespace.

    ingress_secret_instance = None

    if ingress_secret:
        try:
            ingress_secret_instance = core_api.read_namespaced_secret(
                namespace=workshop_namespace, name=ingress_secret
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(
                    f"TLS secret {ingress_secret} is not available for workshop."
                )
            raise

        if not ingress_secret_instance.data.get(
            "tls.crt"
        ) or not ingress_secret_instance.data.get("tls.key"):
            raise kopf.TemporaryError(
                f"TLS secret {ingress_secret} for workshop is not valid."
            )

        ingress_protocol = "https"

    # Calculate which additional applications are enabled for a workshop
    # and provide some helper functions to work with their configuration.

    applications = {}

    if workshop_spec.get("session"):
        applications = workshop_spec["session"].get("applications", {})

    application_defaults = {
        "console": False,
        "docker": False,
        "editor": False,
        "registry": False,
        "slides": True,
        "terminal": True,
        "webdav": False,
    }

    def is_application_enabled(name):
        return applications.get(name, {}).get(
            "enabled", application_defaults.get(name, False)
        )

    def application_property(name, key, default=None):
        properties = applications.get(name, {})
        keys = key.split(".")
        value = default
        for key in keys:
            value = properties.get(key)
            if value is None:
                return default
            properties = value
        return value

    # Create the primary namespace to be used for the workshop session.
    # Make the namespace for the session a child of the custom resource
    # for the session. This way the namespace will be automatically
    # deleted when the resource definition for the session is deleted
    # and we don't have to clean up anything explicitly.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": session_namespace},
    }

    kopf.adopt(namespace_body)

    core_api.create_namespace(body=namespace_body)

    # Create the service account under which the workshop session
    # instance will run. This is created in the workshop namespace. As
    # with the separate namespace, make the session custom resource the
    # parent. We will do this for all objects created for the session as
    # we go along.

    service_account = f"session-{session_id}"

    image_pull_secrets = environment_image_pull_secrets(system_profile)

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": service_account},
        "imagePullSecrets": [
            {"name": pull_secret_name} for pull_secret_name in image_pull_secrets
        ],
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
                "namespace": workshop_namespace,
                "name": service_account,
            }
        ],
    }

    kopf.adopt(cluster_role_binding_body)

    rbac_authorization_api.create_cluster_role_binding(body=cluster_role_binding_body)

    # Setup limit ranges and projects quotas on the primary session namespace.

    role = "admin"
    policy = "default"
    budget = "default"

    if workshop_spec.get("session"):
        role = workshop_spec["session"].get("role", role)
        policy = workshop_spec["session"].get("policy", role)
        budget = workshop_spec["session"].get("budget", budget)

    _setup_limits_and_quotas(
        workshop_namespace, session_namespace, service_account, role, budget,
    )

    # Claim a persistent volume for the workshop session if requested.

    storage = workshop_spec.get("session", {}).get("resources", {}).get("storage")

    if storage:
        persistent_volume_claim_body = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "namespace": workshop_namespace,
                "name": f"{session_namespace}",
            },
            "spec": {
                "accessModes": ["ReadWriteOnce",],
                "resources": {"requests": {"storage": storage,}},
            },
        }

        kopf.adopt(persistent_volume_claim_body)

        core_api.create_namespaced_persistent_volume_claim(
            namespace=workshop_namespace, body=persistent_volume_claim_body
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
            obj = obj.replace("$(session_id)", session_id)
            obj = obj.replace("$(session_namespace)", session_namespace)
            obj = obj.replace("$(service_account)", service_account)
            obj = obj.replace("$(environment_name)", environment_name)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            obj = obj.replace("$(ingress_domain)", ingress_domain)
            obj = obj.replace("$(ingress_protocol)", ingress_protocol)
            obj = obj.replace("$(ingress_secret)", ingress_secret)
            return obj
        elif isinstance(obj, dict):
            return {k: _substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_variables(v) for v in obj]
        else:
            return obj

    objects = []

    if workshop_spec.get("session"):
        objects = workshop_spec["session"].get("objects", [])

    for object_body in objects:
        kind = object_body["kind"]
        api_version = object_body["apiVersion"]

        object_body = _substitute_variables(object_body)

        if not object_body["metadata"].get("namespace"):
            object_body["metadata"]["namespace"] = session_namespace

        kopf.adopt(object_body)

        create_from_dict(object_body)

        if api_version == "v1" and kind.lower() == "namespace":
            annotations = object_body["metadata"].get("annotations", {})

            target_role = annotations.get("training.eduk8s.io/session.role", role)
            target_budget = annotations.get("training.eduk8s.io/session.budget", budget)

            secondary_namespace = object_body["metadata"]["name"]

            _setup_limits_and_quotas(
                workshop_namespace,
                secondary_namespace,
                service_account,
                target_role,
                target_budget,
            )

    # Next setup the deployment resource for the workshop dashboard.

    username = spec["session"].get("username", "")
    password = spec["session"].get("password", "")

    image = workshop_spec.get("content", {}).get(
        "image", "quay.io/eduk8s/workshop-dashboard:master"
    )

    memory = (
        workshop_spec.get("session", {}).get("resources", {}).get("memory", "512Mi")
    )

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": session_namespace},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": session_namespace}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {"labels": {"deployment": session_namespace}},
                "spec": {
                    "serviceAccountName": service_account,
                    "containers": [
                        {
                            "name": "workshop",
                            "image": image,
                            "imagePullPolicy": "Always",
                            "resources": {
                                "requests": {"memory": memory},
                                "limits": {"memory": memory},
                            },
                            "ports": [
                                {
                                    "name": "10080-tcp",
                                    "containerPort": 10080,
                                    "protocol": "TCP",
                                }
                            ],
                            "env": [
                                {
                                    "name": "ENVIRONMENT_NAME",
                                    "value": environment_name,
                                },
                                {
                                    "name": "WORKSHOP_NAMESPACE",
                                    "value": workshop_namespace,
                                },
                                {
                                    "name": "SESSION_NAMESPACE",
                                    "value": session_namespace,
                                },
                                {"name": "AUTH_USERNAME", "value": username,},
                                {"name": "AUTH_PASSWORD", "value": password,},
                                {"name": "INGRESS_DOMAIN", "value": ingress_domain,},
                                {"name": "INGRESS_PROTOCOL", "value": ingress_protocol},
                            ],
                            "volumeMounts": [
                                {
                                    "name": "workshop-config",
                                    "mountPath": "/opt/eduk8s/config",
                                }
                            ],
                        },
                    ],
                    "volumes": [
                        {"name": "workshop-config", "configMap": {"name": "workshop"},}
                    ],
                },
            },
        },
    }

    if storage:
        deployment_body["spec"]["template"]["spec"]["volumes"].append(
            {
                "name": "workshop-data",
                "persistentVolumeClaim": {"claimName": f"{session_namespace}"},
            }
        )

        deployment_body["spec"]["template"]["spec"]["containers"][0][
            "volumeMounts"
        ].append({"name": "workshop-data", "mountPath": "/home/eduk8s"})

    # Apply any patches for the pod specification for the deployment which
    # are specified in the workshop resource definition. This would be used
    # to set resources and setup volumes. If the target item is a list, look
    # for items within that which have a name field that matches a named item
    # in the patch and attempt to merge that with one in the target, but
    # don't do this if the item in the target was added by the patch as
    # that is likely an attempt to deliberately add two named items, such
    # as in the case of volume mounts.

    deployment_patch = {}

    if workshop_spec.get("session"):
        deployment_patch = workshop_spec["session"].get("patches", {})

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
            appended_items = []
            for patch_item in patch:
                if isinstance(patch_item, dict) and "name" in patch_item:
                    for i, target_item in enumerate(target):
                        if (
                            isinstance(target_item, dict)
                            and target_item.get("name") == patch_item["name"]
                            and patch_item["name"] not in appended_items
                        ):
                            _smart_overlay_merge(target[i], patch_item)
                            break
                    else:
                        if patch_item["name"] not in appended_items:
                            appended_items.append(patch_item["name"])
                        target.append(patch_item)
                else:
                    target.append(patch_item)

    if deployment_patch:
        deployment_patch = _substitute_variables(deployment_patch)

        _smart_overlay_merge(
            deployment_body["spec"]["template"]["spec"], deployment_patch
        )

    # Apply any environment variable overrides for the workshop/environment.

    def _apply_environment_patch(patch):
        if not patch:
            return

        patch = _substitute_variables(patch)

        if (
            deployment_body["spec"]["template"]["spec"]["containers"][0].get("env")
            is None
        ):
            deployment_body["spec"]["template"]["spec"]["containers"][0]["env"] = patch
        else:
            _smart_overlay_merge(
                deployment_body["spec"]["template"]["spec"]["containers"][0]["env"],
                patch,
            )

    if workshop_spec.get("session"):
        _apply_environment_patch(workshop_spec["session"].get("env", []))

    _apply_environment_patch(spec["session"].get("env", []))

    # Set environment variable to specify location of workshop content
    # and to denote whether applications are enabled.

    additional_env = []

    files = workshop_spec.get("content", {}).get("files")

    if files:
        additional_env.append({"name": "DOWNLOAD_URL", "value": files})

    for name in application_defaults.keys():
        if is_application_enabled(name):
            additional_env.append({"name": "ENABLE_" + name.upper(), "value": "true"})
        else:
            additional_env.append({"name": "ENABLE_" + name.upper(), "value": "false"})

    # Add in extra configuration for terminal.

    if is_application_enabled("terminal"):
        additional_env.append(
            {
                "name": "TERMINAL_LAYOUT",
                "value": application_property("terminal", "layout", "default"),
            }
        )

    # Add in extra configuation for web console.

    if is_application_enabled("console"):
        additional_env.append(
            {
                "name": "CONSOLE_VENDOR",
                "value": application_property("console", "vendor", "kubernetes"),
            }
        )

        if application_property("console", "vendor", "kubernetes") == "kubernetes":
            secret_body = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": "kubernetes-dashboard-csrf"},
            }

            core_api.create_namespaced_secret(
                namespace=session_namespace, body=secret_body
            )

        if application_property("console", "vendor") == "openshift":
            console_version = application_property(
                "console", "openshift.version", "4.3"
            )
            console_image = (
                applications["console"]
                .get("openshift", {})
                .get("image", f"quay.io/openshift/origin-console:{console_version}")
            )
            console_container = {
                "name": "console",
                "image": console_image,
                "command": ["/opt/bridge/bin/bridge"],
                "env": [
                    {"name": "BRIDGE_K8S_MODE", "value": "in-cluster"},
                    {"name": "BRIDGE_LISTEN", "value": "http://127.0.0.1:10087"},
                    {
                        "name": "BRIDGE_BASE_ADDRESS",
                        "value": f"{ingress_protocol}://{session_namespace}-console/",
                    },
                    {"name": "BRIDGE_PUBLIC_DIR", "value": "/opt/bridge/static"},
                    {"name": "BRIDGE_USER_AUTH", "value": "disabled"},
                    {"name": "BRIDGE_BRANDING", "value": "openshift"},
                ],
                "resources": {
                    "limits": {"memory": "128Mi"},
                    "requests": {"memory": "128Mi"},
                },
            }

            deployment_body["spec"]["template"]["spec"]["containers"].append(
                console_container
            )

    # Add in extra configuration for special cases, as well as bind policy.

    resource_objects = []

    if is_application_enabled("docker"):
        additional_env.append(
            {"name": "DOCKER_HOST", "value": "unix:///var/run/docker/docker.sock",}
        )

        docker_volumes = [
            {"name": "docker-socket", "emptyDir": {}},
            {
                "name": "docker-data",
                "persistentVolumeClaim": {"claimName": f"{session_namespace}-docker"},
            },
        ]

        deployment_body["spec"]["template"]["spec"]["volumes"].extend(docker_volumes)

        docker_workshop_volume_mounts = [
            {
                "name": "docker-socket",
                "mountPath": "/var/run/docker",
                "readOnly": True,
            },
        ]

        deployment_body["spec"]["template"]["spec"]["containers"][0][
            "volumeMounts"
        ].extend(docker_workshop_volume_mounts)

        docker_memory = application_property("docker", "memory", "768Mi")
        docker_storage = application_property("docker", "storage", "5Gi")

        docker_container = {
            "name": "docker",
            "image": "docker:19-dind",
            "securityContext": {"privileged": True, "runAsUser": 0},
            "command": ["dockerd", "--host=unix:///var/run/workshop/docker.sock"],
            "resources": {
                "limits": {"memory": docker_memory},
                "requests": {"memory": docker_memory},
            },
            "volumeMounts": [
                {"name": "docker-socket", "mountPath": "/var/run/workshop",},
                {"name": "docker-data", "mountPath": "/var/lib/docker",},
            ],
        }

        if is_application_enabled("registry"):
            if not ingress_secret:
                docker_container["command"].append(
                    f"--insecure-registry={session_namespace}-registry.{ingress_domain}"
                )

        deployment_body["spec"]["template"]["spec"]["containers"].append(
            docker_container
        )

        resource_objects = [
            {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{session_namespace}-docker",
                },
                "spec": {
                    "accessModes": ["ReadWriteOnce",],
                    "resources": {"requests": {"storage": docker_storage,}},
                },
            },
        ]

    if policy != "custom":
        if is_application_enabled("docker"):
            resource_objects.extend(
                [
                    {
                        "apiVersion": "rbac.authorization.k8s.io/v1",
                        "kind": "RoleBinding",
                        "metadata": {
                            "namespace": workshop_namespace,
                            "name": f"{session_namespace}-docker",
                        },
                        "roleRef": {
                            "apiGroup": "rbac.authorization.k8s.io",
                            "kind": "ClusterRole",
                            "name": f"{workshop_namespace}-docker",
                        },
                        "subjects": [
                            {
                                "kind": "ServiceAccount",
                                "namespace": workshop_namespace,
                                "name": service_account,
                            }
                        ],
                    },
                ]
            )
        else:
            resource_objects.extend(
                [
                    {
                        "apiVersion": "rbac.authorization.k8s.io/v1",
                        "kind": "RoleBinding",
                        "metadata": {
                            "namespace": workshop_namespace,
                            "name": f"{session_namespace}-default",
                        },
                        "roleRef": {
                            "apiGroup": "rbac.authorization.k8s.io",
                            "kind": "ClusterRole",
                            "name": f"{workshop_namespace}-default",
                        },
                        "subjects": [
                            {
                                "kind": "ServiceAccount",
                                "namespace": workshop_namespace,
                                "name": service_account,
                            }
                        ],
                    },
                ]
            )

    for object_body in resource_objects:
        object_body = _substitute_variables(object_body)
        kopf.adopt(object_body)
        create_from_dict(object_body)

    # Add in extra configuration for registry and create session objects.

    if is_application_enabled("registry"):
        characters = string.ascii_letters + string.digits

        registry_username = session_namespace
        registry_password = "".join(random.sample(characters, 32))

        registry_basic_auth = (
            base64.b64encode(f"{registry_username}:{registry_password}".encode("utf-8"))
            .decode("ascii")
            .strip()
        )

        registry_htpasswd_hash = bcrypt.hashpw(
            bytes(registry_password, "ascii"), bcrypt.gensalt(prefix=b"2a")
        ).decode("ascii")

        registry_htpasswd = f"{registry_username}:{registry_htpasswd_hash}\n"

        additional_env.append(
            {
                "name": "REGISTRY_HOST",
                "value": f"{session_namespace}-registry.{ingress_domain}",
            }
        )
        additional_env.append(
            {"name": "REGISTRY_USERNAME", "value": registry_username,}
        )
        additional_env.append(
            {"name": "REGISTRY_PASSWORD", "value": registry_password,}
        )

        registry_volumes = [
            {
                "name": "registry",
                "configMap": {
                    "name": f"{session_namespace}-registry",
                    "items": [{"key": "config.json", "path": "config.json"}],
                },
            },
        ]

        deployment_body["spec"]["template"]["spec"]["volumes"].extend(registry_volumes)

        registry_workshop_volume_mounts = [
            {"name": "registry", "mountPath": "/var/run/registry",},
        ]

        deployment_body["spec"]["template"]["spec"]["containers"][0][
            "volumeMounts"
        ].extend(registry_workshop_volume_mounts)

        registry_memory = application_property("registry", "memory", "768Mi")
        registry_storage = application_property("registry", "storage", "5Gi")

        registry_config = {
            "auths": {
                f"{session_namespace}-registry.{ingress_domain}": {
                    "auth": f"{registry_basic_auth}"
                }
            }
        }

        registry_objects = [
            {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{session_namespace}-registry",
                },
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": registry_storage}},
                },
            },
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{session_namespace}-registry",
                },
                "data": {
                    "htpasswd": registry_htpasswd,
                    "config.json": json.dumps(registry_config, indent=4),
                },
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{session_namespace}-registry",
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": {"deployment": f"{session_namespace}-registry"}
                    },
                    "strategy": {"type": "Recreate"},
                    "template": {
                        "metadata": {
                            "labels": {"deployment": f"{session_namespace}-registry"}
                        },
                        "spec": {
                            "containers": [
                                {
                                    "name": "registry",
                                    "image": "registry.hub.docker.com/library/registry:2.6.1",
                                    "imagePullPolicy": "IfNotPresent",
                                    "resources": {
                                        "limits": {"memory": registry_memory},
                                        "requests": {"memory": registry_memory},
                                    },
                                    "ports": [
                                        {"containerPort": 5000, "protocol": "TCP"}
                                    ],
                                    "env": [
                                        {
                                            "name": "REGISTRY_STORAGE_DELETE_ENABLED",
                                            "value": "true",
                                        },
                                        {"name": "REGISTRY_AUTH", "value": "htpasswd"},
                                        {
                                            "name": "REGISTRY_AUTH_HTPASSWD_REALM",
                                            "value": "Image Registry",
                                        },
                                        {
                                            "name": "REGISTRY_AUTH_HTPASSWD_PATH",
                                            "value": "/auth/htpasswd",
                                        },
                                    ],
                                    "volumeMounts": [
                                        {
                                            "name": "data",
                                            "mountPath": "/var/lib/registry",
                                        },
                                        {"name": "auth", "mountPath": "/auth"},
                                    ],
                                }
                            ],
                            "securityContext": {"runAsUser": 1000},
                            "volumes": [
                                {
                                    "name": "data",
                                    "persistentVolumeClaim": {
                                        "claimName": f"{session_namespace}-registry"
                                    },
                                },
                                {
                                    "name": "auth",
                                    "configMap": {
                                        "name": f"{session_namespace}-registry",
                                        "items": [
                                            {"key": "htpasswd", "path": "htpasswd"}
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                },
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{session_namespace}-registry",
                },
                "spec": {
                    "type": "ClusterIP",
                    "ports": [{"port": 5000, "targetPort": 5000}],
                    "selector": {"deployment": f"{session_namespace}-registry"},
                },
            },
            {
                "apiVersion": "extensions/v1beta1",
                "kind": "Ingress",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{session_namespace}-registry",
                    "annotations": {
                        "nginx.ingress.kubernetes.io/proxy-body-size": "512m"
                    },
                },
                "spec": {
                    "rules": [
                        {
                            "host": f"{session_namespace}-registry.{ingress_domain}",
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "backend": {
                                            "serviceName": f"{session_namespace}-registry",
                                            "servicePort": 5000,
                                        },
                                    }
                                ]
                            },
                        }
                    ],
                },
            },
        ]

        if ingress_secret:
            registry_objects[-1]["spec"]["tls"] = [
                {"hosts": [f"*.{ingress_domain}"], "secretName": ingress_secret,}
            ]

        for object_body in registry_objects:
            object_body = _substitute_variables(object_body)
            kopf.adopt(object_body)
            create_from_dict(object_body)

    # Apply any additional environment variables to the deployment.

    _apply_environment_patch(additional_env)

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
        "metadata": {"name": session_namespace},
        "spec": {
            "type": "ClusterIP",
            "ports": [
                {
                    "name": "10080-tcp",
                    "port": 10080,
                    "protocol": "TCP",
                    "targetPort": 10080,
                }
            ],
            "selector": {"deployment": session_namespace},
        },
    }

    kopf.adopt(service_body)

    core_api.create_namespaced_service(namespace=workshop_namespace, body=service_body)

    # Create the ingress for the workshop, including any for extra named
    # named ingresses.

    ingress_rules = [
        {
            "host": session_hostname,
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "backend": {
                            "serviceName": session_namespace,
                            "servicePort": 10080,
                        },
                    }
                ]
            },
        }
    ]

    ingresses = []
    ingress_hostnames = []

    applications = {}

    if workshop_spec.get("session"):
        applications = workshop_spec["session"].get("applications", {})
        ingresses = workshop_spec["session"].get("ingresses", [])

    if applications:
        if applications.get("console", {}).get("enabled", True):
            ingress_hostnames.append(f"{session_namespace}-console.{ingress_domain}")
        if applications.get("editor", {}).get("enabled", False):
            ingress_hostnames.append(f"{session_namespace}-editor.{ingress_domain}")

    for ingress in ingresses:
        ingress_hostnames.append(
            f"{session_namespace}-{ingress['name']}.{ingress_domain}"
        )

    for ingress_hostname in ingress_hostnames:
        ingress_rules.append(
            {
                "host": ingress_hostname,
                "http": {
                    "paths": [
                        {
                            "path": "/",
                            "backend": {
                                "serviceName": session_namespace,
                                "servicePort": 10080,
                            },
                        }
                    ]
                },
            }
        )

    ingress_body = {
        "apiVersion": "extensions/v1beta1",
        "kind": "Ingress",
        "metadata": {
            "name": session_namespace,
            "annotations": {
                "nginx.ingress.kubernetes.io/enable-cors": "true",
                "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600",
                "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
                "projectcontour.io/websocket-routes": "/",
                "projectcontour.io/response-timeout": "3600",
            },
        },
        "spec": {"rules": ingress_rules,},
    }

    if ingress_secret:
        ingress_body["spec"]["tls"] = [
            {"hosts": [f"*.{ingress_domain}"], "secretName": ingress_secret,}
        ]

    if ingress_class:
        ingress_body["metadata"]["annotations"][
            "kubernetes.io/ingress.class"
        ] = ingress_class

    kopf.adopt(ingress_body)

    extensions_api.create_namespaced_ingress(
        namespace=workshop_namespace, body=ingress_body
    )

    url = f"{ingress_protocol}://{session_hostname}"

    return {"url": url}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshopsessions", optional=True)
def workshop_session_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
