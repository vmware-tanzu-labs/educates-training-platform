import time
import random
import string
import base64
import json
import copy

import bcrypt

import kopf
import pykube
import yaml

from .objects import create_from_dict, WorkshopEnvironment
from .helpers import Applications

from .config import (
    resolve_workshop_image,
    OPERATOR_API_GROUP,
    OPERATOR_STATUS_KEY,
    OPERATOR_NAME_PREFIX,
    IMAGE_REPOSITORY,
    INGRESS_DOMAIN,
    INGRESS_PROTOCOL,
    INGRESS_SECRET,
    INGRESS_CLASS,
    CLUSTER_STORAGE_CLASS,
    CLUSTER_STORAGE_USER,
    CLUSTER_STORAGE_GROUP,
    CLUSTER_SECURITY_POLICY_ENGINE,
    DOCKERD_MTU,
    DOCKERD_ROOTLESS,
    DOCKERD_PRIVILEGED,
    DOCKERD_MIRROR_REMOTE,
    NETWORK_BLOCKCIDRS,
    GOOGLE_TRACKING_ID,
    DOCKER_IN_DOCKER_IMAGE,
    DOCKER_REGISTRY_IMAGE,
)

__all__ = ["workshop_session_create", "workshop_session_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


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
                        "max": {"cpu": "8", "memory": "12Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "8", "memory": "12Gi"},
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
                "hard": {"limits.cpu": "8", "limits.memory": "12Gi"},
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
                "hard": {"limits.cpu": "8", "limits.memory": "12Gi"},
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
                        "max": {"cpu": "8", "memory": "16Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "8", "memory": "16Gi"},
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
                "hard": {"limits.cpu": "8", "limits.memory": "16Gi"},
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
                "hard": {"limits.cpu": "8", "limits.memory": "16Gi"},
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


def _smart_overlay_merge(target, patch, attr="name"):
    if isinstance(patch, dict):
        for key, value in patch.items():
            if key not in target:
                target[key] = value
            elif type(target[key]) != type(value):
                target[key] = value
            elif isinstance(value, (dict, list)):
                _smart_overlay_merge(target[key], value, attr)
            else:
                target[key] = value
    elif isinstance(patch, list):
        appended_items = []
        for patch_item in patch:
            if isinstance(patch_item, dict) and attr in patch_item:
                for i, target_item in enumerate(target):
                    if (
                        isinstance(target_item, dict)
                        and target_item.get(attr) == patch_item[attr]
                        and patch_item[attr] not in appended_items
                    ):
                        _smart_overlay_merge(target[i], patch_item, attr)
                        break
                else:
                    if patch_item[attr] not in appended_items:
                        appended_items.append(patch_item[attr])
                    target.append(patch_item)
            else:
                target.append(patch_item)


def _setup_session_namespace(
    workshop_name,
    portal_name,
    environment_name,
    session_name,
    workshop_namespace,
    session_namespace,
    target_namespace,
    service_account,
    applications,
    role,
    budget,
    limits,
    security_policy,
):
    # When a namespace is created, it needs to be populated with the default
    # service account, as well as potentially resource quotas and limit ranges.
    # If those aren't created immediately, some of the following steps may fail.
    # At least try to wait for the default service account to be created as it
    # must always exist. Others are more problematic since they may or may not
    # exist.

    for _ in range(25):
        try:
            service_account_instance = pykube.ServiceAccount.objects(
                api, namespace=target_namespace
            ).get(name="default")

        except pykube.exceptions.ObjectDoesNotExist:
            time.sleep(0.1)

        else:
            break

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

        if limits:
            resource_limits_definition = copy.deepcopy(resource_limits_definition)

            container_limits_patch = {"type": "Container"}
            container_limits_patch.update(limits)

            _smart_overlay_merge(
                resource_limits_definition["spec"]["limits"],
                [container_limits_patch],
                "type",
            )

    # Delete any limit ranges applied to the namespace that may conflict with
    # the limit range being applied. For the case of custom, we delete any being
    # applied but don't replace it. It is assumed that the session objects for
    # the workshop will define any limit ranges and resource quotas itself.

    if budget != "default":
        for limit_range in pykube.LimitRange.objects(
            api, namespace=target_namespace
        ).all():
            try:
                limit_range.delete()
            except pykube.exceptions.ObjectDoesNotExist:
                pass

    # Delete any resource quotas applied to the namespace that may conflict with
    # the resource quotas being applied.

    if budget != "default":
        for resource_quota in pykube.ResourceQuota.objects(
            api, namespace=target_namespace
        ).all():
            try:
                resource_quota.delete()
            except pykube.exceptions.ObjectDoesNotExist:
                pass

    # If there is a CIDR list of networks to block create a network policy in
    # the target session environment to restrict access from all pods. The
    # customised roles for "admin", "edit" and "view" used below ensure that the
    # network policy objects cannot be deleted from the session namespaces by a
    # user.

    if NETWORK_BLOCKCIDRS:
        network_policy_body = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"{OPERATOR_NAME_PREFIX}-network-policy",
                "namespace": target_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "spec": {
                "policyTypes": ["Egress"],
                "egress": [],
            },
        }

        egresses = []

        ipv4_blockcidrs = []
        ipv6_blockcidrs = []

        for block in NETWORK_BLOCKCIDRS:
            if ":" in block:
                ipv6_blockcidrs.append(block)
            else:
                ipv4_blockcidrs.append(block)

        if ipv4_blockcidrs:
            egresses.append(
                {"to": [{"ipBlock": {"cidr": "0.0.0.0/0", "except": ipv4_blockcidrs}}]}
            )

        if ipv6_blockcidrs:
            egresses.append(
                {"to": [{"ipBlock": {"cidr": "::/0", "except": ipv6_blockcidrs}}]}
            )

        network_policy_body["spec"]["egress"] = egresses

        kopf.adopt(network_policy_body)

        NetworkPolicy = pykube.object_factory(
            api, "networking.k8s.io/v1", "NetworkPolicy"
        )

        NetworkPolicy(api, network_policy_body).create()

    # Create role binding in the namespace so the service account under which
    # the workshop environment runs can create resources in it. We only allow a
    # select set of roles which are "admin", "edit", "view" and "cluster-admin".
    # Except for "cluster-admin" these will be mapped to our own version of the
    # respective cluster roles which have any edit access to network policies
    # dropped. If a role is provided we don't know about, we will map it to
    # "view" which because it is the most restrictive will flag more easily that
    # something is wrong in what a workshop defines. If want no role at all to
    # be set up so you can define your own, then can set "custom".

    role_mappings = {
        "admin": f"{OPERATOR_NAME_PREFIX}-admin-session-role",
        "edit": f"{OPERATOR_NAME_PREFIX}-edit-session-role",
        "view": f"{OPERATOR_NAME_PREFIX}-view-session-role",
        "cluster-admin": "cluster-admin",
        "custom": None,
    }

    role_resource_name = role_mappings.get(role)

    if role_resource_name is None and role != "custom":
        role_resource_name = f"{OPERATOR_NAME_PREFIX}-view-session-role"

    if role_resource_name is not None:
        role_binding_body = {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": f"{OPERATOR_NAME_PREFIX}-session-role",
                "namespace": target_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": role_resource_name,
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": service_account,
                    "namespace": workshop_namespace,
                }
            ],
        }

        pykube.RoleBinding(api, role_binding_body).create()

    # Create rolebinding so that all service accounts in the namespace are bound
    # by the specified pod security policy.

    if CLUSTER_SECURITY_POLICY_ENGINE == "pod-security-policies":
        psp_role_binding_body = {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": f"{OPERATOR_NAME_PREFIX}-security-policy",
                "namespace": target_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": f"{OPERATOR_NAME_PREFIX}-{security_policy}-psp",
            },
            "subjects": [
                {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "Group",
                    "name": f"system:serviceaccounts:{target_namespace}",
                }
            ],
        }

        pykube.RoleBinding(api, psp_role_binding_body).create()

    # Create secret which holds image registry '.docker/config.json' and apply
    # it to the default service account in the target namespace so that any
    # deployment using that service account can pull images from the image
    # registry without needing to explicitly add their own image pull secret.

    if applications.is_enabled("registry"):
        registry_host = applications.property("registry", "host")
        registry_username = applications.property("registry", "username")
        registry_password = applications.property("registry", "password")
        registry_secret = applications.property("registry", "secret")

        registry_basic_auth = (
            base64.b64encode(f"{registry_username}:{registry_password}".encode("utf-8"))
            .decode("ascii")
            .strip()
        )

        registry_config = {"auths": {registry_host: {"auth": f"{registry_basic_auth}"}}}

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": registry_secret,
                "namespace": target_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "type": "kubernetes.io/dockerconfigjson",
            "stringData": {".dockerconfigjson": json.dumps(registry_config, indent=4)},
        }

        pykube.Secret(api, secret_body).create()

    # Create limit ranges for the namespace so any deployments will have default
    # memory/cpu min and max values.

    if budget not in ("default", "custom"):
        resource_limits_body = copy.deepcopy(resource_limits_definition)

        resource_limits_body["metadata"].setdefault("labels", {}).update(
            {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            }
        )

        resource_limits_body["metadata"]["namespace"] = target_namespace

        pykube.LimitRange(api, resource_limits_body).create()

    # Create resource quotas for the namespace so there is a maximum for what
    # resources can be used.

    if budget not in ("default", "custom"):
        resource_quota_body = copy.deepcopy(compute_resources_definition)

        resource_quota_body["metadata"].setdefault("labels", {}).update(
            {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            }
        )

        resource_quota_body["metadata"]["namespace"] = target_namespace

        pykube.ResourceQuota(api, resource_quota_body).create()

        resource_quota_body = copy.deepcopy(compute_resources_timebound_definition)

        resource_quota_body["metadata"].setdefault("labels", {}).update(
            {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            }
        )

        resource_quota_body["metadata"]["namespace"] = target_namespace

        pykube.ResourceQuota(api, resource_quota_body).create()

        resource_quota_body = copy.deepcopy(object_counts_definition)

        resource_quota_body["metadata"].setdefault("labels", {}).update(
            {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            }
        )

        resource_quota_body["metadata"]["namespace"] = target_namespace

        pykube.ResourceQuota(api, resource_quota_body).create()

        # Verify that the status of the resource quotas have been updated. If we
        # don't do this, then the calculated hard limits may not be calculated
        # before we start creating resources in the namespace resulting in a
        # failure. If we can't manage to verify quotas after a period, give up.
        # This may result in a subsequent failure.

        for _ in range(25):
            resource_quotas = pykube.ResourceQuota.objects(
                api, namespace=target_namespace
            ).all()

            for resource_quota in resource_quotas:
                if not resource_quota.obj.get("status") or not resource_quota.obj[
                    "status"
                ].get("hard"):
                    time.sleep(0.1)
                    continue

            break


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1beta1",
    "workshopsessions",
    id=OPERATOR_STATUS_KEY,
)
def workshop_session_create(name, meta, spec, status, patch, logger, **_):
    # The namespace created for the session is the name of the workshop
    # namespace suffixed by the session ID. By convention this should be
    # the same as what would be used for the name of the session
    # resource definition, but we can't rely on that being the case, as
    # may be different during development and testing, so we construct
    # the name ourself.

    environment_name = spec["environment"]["name"]
    environment_name = spec["environment"]["name"]

    workshop_namespace = environment_name

    session_name = name

    try:
        environment_instance = WorkshopEnvironment.objects(api).get(
            name=workshop_namespace
        )

    except pykube.exceptions.ObjectDoesNotExist:
        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(f"Environment {workshop_namespace} does not exist.")

    session_id = spec["session"]["id"]
    session_namespace = f"{workshop_namespace}-{session_id}"

    # Can optionally be passed name of the training portal via a label
    # when the workshop environment is created as a child to a training
    # portal.

    portal_name = meta.get("labels", {}).get(
        f"training.{OPERATOR_API_GROUP}/portal.name", ""
    )

    # We pull details of the workshop to be deployed from the status of
    # the workspace custom resource. This is a copy of the specification
    # from the custom resource for the workshop. We use a copy so we
    # aren't affected by changes in the original workshop made after the
    # workspace was created.

    if not environment_instance.obj.get("status") or not environment_instance.obj[
        "status"
    ].get(OPERATOR_STATUS_KEY):
        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(f"Environment {workshop_namespace} is not ready.")

    workshop_name = environment_instance.obj["status"][OPERATOR_STATUS_KEY]["workshop"][
        "name"
    ]
    workshop_spec = environment_instance.obj["status"][OPERATOR_STATUS_KEY]["workshop"][
        "spec"
    ]

    # Create a wrapper for determining if applications enabled and what
    # configuration they provide.

    applications = Applications(workshop_spec["session"].get("applications", {}))

    # Calculate the hostname to be used for this workshop session.

    session_hostname = f"{session_namespace}.{INGRESS_DOMAIN}"

    # Calculate role, security policy and quota details for primary namespace.

    role = "admin"
    budget = "default"
    limits = {}

    namespace_security_policy = "nonroot"

    security_policy_mapping = {
        "restricted": "restricted",
        "baseline": "baseline",
        "privileged": "privileged",
        # Following are obsolete and should not be used.
        "nonroot": "restricted",
        "anyuid": "baseline",
        "custom": "privileged",
    }

    def resolve_security_policy(name):
        return security_policy_mapping.get(name, "restricted")

    if workshop_spec.get("session"):
        role = workshop_spec["session"].get("namespaces", {}).get("role", role)
        budget = workshop_spec["session"].get("namespaces", {}).get("budget", budget)
        limits = workshop_spec["session"].get("namespaces", {}).get("limits", limits)

        namespace_security_policy = resolve_security_policy(
            workshop_spec["session"]
            .get("namespaces", {})
            .get("security", {})
            .get("policy", namespace_security_policy)
        )

    # Calculate a random password for the image registry and git server
    # applications if required.

    characters = string.ascii_letters + string.digits

    if applications.is_enabled("registry"):
        registry_host = f"registry-{session_namespace}.{INGRESS_DOMAIN}"
        registry_username = session_namespace
        registry_password = "".join(random.sample(characters, 32))
        registry_secret = f"{OPERATOR_NAME_PREFIX}-registry-credentials"

        applications.properties("registry")["host"] = registry_host
        applications.properties("registry")["username"] = registry_username
        applications.properties("registry")["password"] = registry_password
        applications.properties("registry")["secret"] = registry_secret

    if applications.is_enabled("git"):
        git_host = f"git-{session_namespace}.{INGRESS_DOMAIN}"
        git_username = session_namespace
        git_password = "".join(random.sample(characters, 32))

        applications.properties("git")["host"] = git_host
        applications.properties("git")["username"] = git_username
        applications.properties("git")["password"] = git_password

    # Determine if any secrets being copied into the workshop environment
    # namespace exist. This is done before creating the session namespace so we
    # can fail with a transient error and try again later. Note that we don't
    # check whether any secrets required for workshop downloads are included
    # in this list and will instead let the download of workshop content fail
    # in the running container if any fail so users can know there was a
    # problem.

    environment_secrets = {}

    for secret_item in workshop_spec.get("environment", {}).get("secrets", []):
        try:
            secret = pykube.Secret.objects(api, namespace=workshop_namespace).get(
                name=secret_item["name"]
            )

        except pykube.exceptions.ObjectDoesNotExist:
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Secret {secret_item['name']} not yet available in {workshop_namespace}.",
                delay=15,
            )

        except pykube.exceptions.KubernetesError as e:
            logger.exception(
                f"Unexpected error querying secrets in {workshop_namespace}."
            )
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Unexpected error querying secrets in {workshop_namespace}."
            )

        # This will go into a secret later, so we base64 encode values and set
        # keys to be file names to be used when mounted into the container
        # filesystem via a projected volume. Drop the manage fields property
        # so not so much noise.

        secret_obj = copy.deepcopy(secret.obj)
        secret_obj["metadata"].pop("managedFields", None)
        environment_secrets[f"{secret_item['name']}.yaml"] = base64.b64encode(
            yaml.dump(secret_obj, Dumper=yaml.Dumper).encode("utf-8")
        ).decode("utf-8")

    # Create the primary namespace to be used for the workshop session.
    # Make the namespace for the session a child of the custom resource
    # for the session. This way the namespace will be automatically
    # deleted when the resource definition for the session is deleted
    # and we don't have to clean up anything explicitly.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": session_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                f"training.{OPERATOR_API_GROUP}/policy.engine": CLUSTER_SECURITY_POLICY_ENGINE,
                f"training.{OPERATOR_API_GROUP}/policy.name": namespace_security_policy,
            },
            "annotations": {"secretgen.carvel.dev/excluded-from-wildcard-matching": ""},
        },
    }

    if CLUSTER_SECURITY_POLICY_ENGINE == "pod-security":
        namespace_body["metadata"]["labels"][
            "pod-security.kubernetes.io/enforce"
        ] = namespace_security_policy

    kopf.adopt(namespace_body)

    try:
        pykube.Namespace(api, namespace_body).create()

    except pykube.exceptions.PyKubeError as e:
        if e.code == 409:
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(f"Namespace {session_namespace} already exists.")
        raise

    # Create the service account under which the workshop session
    # instance will run. This is created in the workshop namespace. As
    # with the separate namespace, make the session custom resource the
    # parent. We will do this for all objects created for the session as
    # we go along. Name the service account the same as the session
    # namespace now even though this includes the workshop environment
    # name and is contained in the workshop environment.

    service_account = session_namespace

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": service_account,
            "namespace": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            },
        },
    }

    kopf.adopt(service_account_body)

    pykube.ServiceAccount(api, service_account_body).create()

    # Create the rolebinding for this service account to add access to
    # the additional roles that the Kubernetes web console requires.

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": f"{OPERATOR_NAME_PREFIX}-web-console-{session_namespace}",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{OPERATOR_NAME_PREFIX}-web-console-{workshop_namespace}",
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

    pykube.ClusterRoleBinding(api, cluster_role_binding_body).create()

    # Setup configuration on the primary session namespace.

    _setup_session_namespace(
        workshop_name,
        portal_name,
        environment_name,
        session_name,
        workshop_namespace,
        session_namespace,
        session_namespace,
        service_account,
        applications,
        role,
        budget,
        limits,
        namespace_security_policy,
    )

    # Claim a persistent volume for the workshop session if requested.

    storage = workshop_spec.get("session", {}).get("resources", {}).get("storage")

    if storage:
        persistent_volume_claim_body = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{session_namespace}",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "spec": {
                "accessModes": [
                    "ReadWriteOnce",
                ],
                "resources": {
                    "requests": {
                        "storage": storage,
                    }
                },
            },
        }

        if CLUSTER_STORAGE_CLASS:
            persistent_volume_claim_body["spec"][
                "storageClassName"
            ] = CLUSTER_STORAGE_CLASS

        kopf.adopt(persistent_volume_claim_body)

        pykube.PersistentVolumeClaim(api, persistent_volume_claim_body).create()

    # Helper function to replace variables in values for objects etc.

    def _substitute_variables(obj):
        if isinstance(obj, str):
            obj = obj.replace("$(image_repository)", IMAGE_REPOSITORY)
            obj = obj.replace("$(session_id)", session_id)
            obj = obj.replace("$(session_namespace)", session_namespace)
            obj = obj.replace("$(service_account)", service_account)
            obj = obj.replace("$(environment_name)", environment_name)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            obj = obj.replace("$(ingress_domain)", INGRESS_DOMAIN)
            obj = obj.replace("$(ingress_protocol)", INGRESS_PROTOCOL)
            obj = obj.replace("$(ingress_port_suffix)", "")
            obj = obj.replace("$(ingress_secret)", INGRESS_SECRET)
            obj = obj.replace("$(ingress_class)", INGRESS_CLASS)
            obj = obj.replace("$(storage_class)", CLUSTER_STORAGE_CLASS)
            if applications.is_enabled("registry"):
                obj = obj.replace("$(registry_host)", registry_host)
                obj = obj.replace("$(registry_username)", registry_username)
                obj = obj.replace("$(registry_password)", registry_password)
                obj = obj.replace("$(registry_secret)", registry_secret)
            if applications.is_enabled("git"):
                obj = obj.replace("$(git_protocol)", INGRESS_PROTOCOL)
                obj = obj.replace("$(git_host)", git_host)
                obj = obj.replace("$(git_username)", git_username)
                obj = obj.replace("$(git_password)", git_password)
            return obj
        elif isinstance(obj, dict):
            return {k: _substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_variables(v) for v in obj]
        else:
            return obj

    # Create any secondary namespaces required for the session.

    namespaces = []

    if workshop_spec.get("session"):
        namespaces = workshop_spec["session"].get("namespaces", {}).get("secondary", [])
        for namespaces_item in namespaces:
            target_namespace = _substitute_variables(namespaces_item["name"])

            target_role = namespaces_item.get("role", role)
            target_budget = namespaces_item.get("budget", budget)
            target_limits = namespaces_item.get("limits", {})

            target_security_policy = resolve_security_policy(
                namespaces_item.get("security", {}).get(
                    "policy", namespace_security_policy
                )
            )

            namespace_body = {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": target_namespace,
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "session",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                        f"training.{OPERATOR_API_GROUP}/policy.engine": CLUSTER_SECURITY_POLICY_ENGINE,
                        f"training.{OPERATOR_API_GROUP}/policy.name": target_security_policy,
                    },
                    "annotations": {
                        "secretgen.carvel.dev/excluded-from-wildcard-matching": ""
                    },
                },
            }

            if CLUSTER_SECURITY_POLICY_ENGINE == "pod-security":
                namespace_body["metadata"]["labels"][
                    "pod-security.kubernetes.io/enforce"
                ] = target_security_policy

            kopf.adopt(namespace_body)

            try:
                pykube.Namespace(api, namespace_body).create()

            except pykube.exceptions.PyKubeError as e:
                if e.code == 409:
                    patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
                    raise kopf.TemporaryError(
                        f"Namespace {target_namespace} already exists."
                    )
                raise

            _setup_session_namespace(
                workshop_name,
                portal_name,
                environment_name,
                session_name,
                workshop_namespace,
                session_namespace,
                target_namespace,
                service_account,
                applications,
                target_role,
                target_budget,
                target_limits,
                target_security_policy,
            )

    # Create any additional resource objects required for the session.
    #
    # XXX For now make the session resource definition the parent of
    # all objects. Technically should only do so for non namespaced
    # objects, or objects created in namespaces that already existed.
    # How to work out if a resource type is namespaced or not with the
    # Python Kubernetes client appears to be a bit of a hack.

    objects = []

    if workshop_spec.get("session"):
        objects = workshop_spec["session"].get("objects", [])

    for object_body in objects:
        kind = object_body["kind"]
        api_version = object_body["apiVersion"]

        object_body = _substitute_variables(object_body)

        if not object_body["metadata"].get("namespace"):
            object_body["metadata"]["namespace"] = session_namespace

        object_body["metadata"].setdefault("labels", {}).update(
            {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                f"training.{OPERATOR_API_GROUP}/session.objects": "true",
            }
        )

        kopf.adopt(object_body)

        if api_version == "v1" and kind.lower() == "namespace":
            annotations = object_body["metadata"].get("annotations", {})

            target_role = annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.role", role
            )

            target_security_policy = resolve_security_policy(
                annotations.get(
                    f"training.{OPERATOR_API_GROUP}/session.security.policy",
                    namespace_security_policy,
                )
            )

            object_body["metadata"].setdefault("labels", {}).update(
                {
                    f"training.{OPERATOR_API_GROUP}/policy.engine": CLUSTER_SECURITY_POLICY_ENGINE,
                    f"training.{OPERATOR_API_GROUP}/policy.name": target_security_policy,
                }
            )

            if CLUSTER_SECURITY_POLICY_ENGINE == "pod-security":
                object_body["metadata"]["labels"][
                    "pod-security.kubernetes.io/enforce"
                ] = target_security_policy

            target_budget = annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.budget", budget
            )

            target_limits = {}

            if annotations.get(f"training.{OPERATOR_API_GROUP}/session.limits.min.cpu"):
                target_limits.setdefault("min", {})["cpu"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.min.cpu"
                ]
            if annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.limits.min.memory"
            ):
                target_limits.setdefault("min", {})["memory"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.min.memory"
                ]

            if annotations.get(f"training.{OPERATOR_API_GROUP}/session.limits.max.cpu"):
                target_limits.setdefault("max", {})["cpu"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.max.cpu"
                ]
            if annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.limits.max.memory"
            ):
                target_limits.setdefault("max", {})["memory"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.max.memory"
                ]

            if annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.limits.defaultrequest.cpu"
            ):
                target_limits.setdefault("defaultRequest", {})["cpu"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.defaultrequest.cpu"
                ]
            if annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.limits.defaultrequest.memory"
            ):
                target_limits.setdefault("defaultRequest", {})["memory"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.defaultrequest.memory"
                ]

            if annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.limits.default.cpu"
            ):
                target_limits.setdefault("default", {})["cpu"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.default.cpu"
                ]
            if annotations.get(
                f"training.{OPERATOR_API_GROUP}/session.limits.default.memory"
            ):
                target_limits.setdefault("default", {})["memory"] = annotations[
                    f"training.{OPERATOR_API_GROUP}/session.limits.default.memory"
                ]

            create_from_dict(object_body)

            target_namespace = object_body["metadata"]["name"]

            _setup_session_namespace(
                workshop_name,
                portal_name,
                environment_name,
                session_name,
                workshop_namespace,
                session_namespace,
                target_namespace,
                service_account,
                applications,
                target_role,
                target_budget,
                target_limits,
                target_security_policy,
            )

        else:
            create_from_dict(object_body)

        if api_version == "v1" and kind.lower() == "resourcequota":
            # Verify that the status of the resource quota has been
            # updated. If we don't do this, then the calculated hard
            # limits may not be calculated before we start creating
            # resources in the namespace resulting in a failure. If we
            # can't manage to verify quotas after a period, give up.
            # This may result in a subsequent failure.

            for _ in range(25):
                resource_quota = pykube.ResourceQuota.objects(
                    api, namespace=object_body["metadata"]["namespace"]
                ).get(name=object_body["metadata"]["name"])

                if not resource_quota.obj.get("status") or not resource_quota.obj[
                    "status"
                ].get("hard"):
                    time.sleep(0.1)
                    continue

    # Next setup the deployment resource for the workshop dashboard. Note that
    # spec.content.image is deprecated and should use spec.workshop.image. We
    # will check both.

    username = spec["session"].get("username", "")
    password = spec["session"].get("password", "")

    workshop_image = resolve_workshop_image(
        workshop_spec.get("workshop", {}).get(
            "image", workshop_spec.get("content", {}).get("image", "base-environment:*")
        )
    )

    default_memory = "512Mi"

    if applications.is_enabled("editor"):
        default_memory = "1Gi"

    workshop_memory = (
        workshop_spec.get("session", {})
        .get("resources", {})
        .get("memory", default_memory)
    )

    image_pull_policy = "IfNotPresent"

    google_tracking_id = (
        spec.get("analytics", {})
        .get("google", {})
        .get("trackingId", GOOGLE_TRACKING_ID)
    )

    if (
        workshop_image.endswith(":main")
        or workshop_image.endswith(":master")
        or workshop_image.endswith(":develop")
        or workshop_image.endswith(":latest")
        or ":" not in workshop_image
    ):
        image_pull_policy = "Always"

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": session_namespace,
            "namespace": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                f"training.{OPERATOR_API_GROUP}/session.services.workshop": "true",
            },
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": session_namespace}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {
                    "labels": {
                        "deployment": session_namespace,
                        f"training.{OPERATOR_API_GROUP}/component": "session",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                        f"training.{OPERATOR_API_GROUP}/session.services.workshop": "true",
                    },
                },
                "spec": {
                    "serviceAccountName": service_account,
                    "securityContext": {
                        "fsGroup": CLUSTER_STORAGE_GROUP,
                        "supplementalGroups": [CLUSTER_STORAGE_GROUP],
                    },
                    "initContainers": [],
                    "containers": [
                        {
                            "name": "workshop",
                            "image": workshop_image,
                            "imagePullPolicy": image_pull_policy,
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "capabilities": {"drop": ["ALL"]},
                                "runAsNonRoot": True,
                                "seccompProfile": {"type": "RuntimeDefault"},
                            },
                            "resources": {
                                "requests": {"memory": workshop_memory},
                                "limits": {"memory": workshop_memory},
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
                                    "name": "GOOGLE_TRACKING_ID",
                                    "value": google_tracking_id,
                                },
                                {
                                    "name": "ENVIRONMENT_NAME",
                                    "value": environment_name,
                                },
                                {
                                    "name": "WORKSHOP_NAME",
                                    "value": workshop_name,
                                },
                                {
                                    "name": "WORKSHOP_NAMESPACE",
                                    "value": workshop_namespace,
                                },
                                {
                                    "name": "SESSION_NAMESPACE",
                                    "value": session_namespace,
                                },
                                {
                                    "name": "SESSION_ID",
                                    "value": session_id,
                                },
                                {
                                    "name": "AUTH_USERNAME",
                                    "value": username,
                                },
                                {
                                    "name": "AUTH_PASSWORD",
                                    "value": password,
                                },
                                {
                                    "name": "INGRESS_DOMAIN",
                                    "value": INGRESS_DOMAIN,
                                },
                                {"name": "INGRESS_PROTOCOL", "value": INGRESS_PROTOCOL},
                                {
                                    "name": "IMAGE_REPOSITORY",
                                    "value": IMAGE_REPOSITORY,
                                },
                                {"name": "INGRESS_CLASS", "value": INGRESS_CLASS},
                                {
                                    "name": "STORAGE_CLASS",
                                    "value": CLUSTER_STORAGE_CLASS,
                                },
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
                        {
                            "name": "workshop-config",
                            "configMap": {"name": "workshop"},
                        }
                    ],
                    "hostAliases": [],
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
        ].append(
            {"name": "workshop-data", "mountPath": "/home/eduk8s", "subPath": "home"}
        )

        if CLUSTER_STORAGE_USER:
            # This hack is to cope with Kubernetes clusters which don't properly
            # set up persistent volume ownership. IBM Kubernetes is one example.
            # The init container runs as root and sets permissions on the
            # storage and ensures it is group writable. Note that this will only
            # work where pod security policies are not enforced. Don't attempt
            # to use it if they are. If they are, this hack should not be
            # required.

            storage_init_container = {
                "name": "storage-permissions-initialization",
                "image": workshop_image,
                "imagePullPolicy": image_pull_policy,
                "securityContext": {
                    "allowPrivilegeEscalation": False,
                    "capabilities": {"drop": ["ALL"]},
                    "runAsNonRoot": False,
                    "runAsUser": 0,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "command": ["/bin/sh", "-c"],
                "args": [
                    f"chown {CLUSTER_STORAGE_USER}:{CLUSTER_STORAGE_GROUP} /mnt && chmod og+rwx /mnt"
                ],
                "resources": {
                    "requests": {"memory": workshop_memory},
                    "limits": {"memory": workshop_memory},
                },
                "volumeMounts": [{"name": "workshop-data", "mountPath": "/mnt"}],
            }

            deployment_body["spec"]["template"]["spec"]["initContainers"].append(
                storage_init_container
            )

        storage_init_container = {
            "name": "workshop-volume-initialization",
            "image": workshop_image,
            "imagePullPolicy": image_pull_policy,
            "securityContext": {
                "allowPrivilegeEscalation": False,
                "capabilities": {"drop": ["ALL"]},
                "runAsNonRoot": True,
                "seccompProfile": {"type": "RuntimeDefault"},
            },
            "command": [
                "/opt/eduk8s/sbin/setup-volume",
                "/home/eduk8s",
                "/mnt/home",
            ],
            "resources": {
                "requests": {"memory": workshop_memory},
                "limits": {"memory": workshop_memory},
            },
            "volumeMounts": [{"name": "workshop-data", "mountPath": "/mnt"}],
        }

        deployment_body["spec"]["template"]["spec"]["initContainers"].append(
            storage_init_container
        )

    # Work out whether workshop downloads require any secrets and if so we
    # create an init container and perform workshop downloads from that rather
    # than the main container so we don't need to expose secrets to the workshop
    # user.

    def vendir_secrets_required(contents):
        for content in contents:
            if content.get("git", {}).get("secretRef"):
                return True
            if (
                content.get("git", {})
                .get("verification", {})
                .get("publicKeysSecretRef")
            ):
                return True
            elif content.get("hg", {}).get("secretRef"):
                return True
            elif content.get("http", {}).get("secretRef"):
                return True
            elif content.get("image", {}).get("secretRef"):
                return True
            elif content.get("imgpkgBundle", {}).get("secretRef"):
                return True
            elif content.get("githubRelease", {}).get("secretRef"):
                return True
            elif content.get("helmChart", {}).get("repository", {}).get("secretRef"):
                return True
            elif content.get("inline", {}).get("pathsFrom", []):
                return True

    workshop_files = workshop_spec.get("workshop", {}).get("files", [])

    need_secrets = vendir_secrets_required(workshop_files)

    if not need_secrets:
        for package in workshop_spec.get("workshop", {}).get("packages", []):
            package_files = package.get("files", [])
            need_secrets = vendir_secrets_required(package_files)
            if need_secrets:
                break

    if need_secrets and environment_secrets:
        # Need download secrets, so we need create a new secret which is a
        # composite of all the other secrets so we can mount the full Kubernetes
        # resource definitions for the secrets into the init container.

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{session_namespace}-vendir-secrets",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "data": environment_secrets,
        }

        kopf.adopt(secret_body)

        pykube.Secret(api, secret_body).create()

        deployment_body["spec"]["template"]["spec"]["volumes"].extend(
            [
                {"name": "assets-data", "emptyDir": {}},
                {"name": "packages-data", "emptyDir": {}},
                {
                    "name": "vendir-secrets",
                    "secret": {"secretName": f"{session_namespace}-vendir-secrets"},
                },
            ]
        )

        deployment_body["spec"]["template"]["spec"]["containers"][0][
            "volumeMounts"
        ].extend(
            [
                {"name": "assets-data", "mountPath": "/opt/assets"},
                {"name": "packages-data", "mountPath": "/opt/packages"},
            ]
        )

        downloads_init_container = {
            "name": "workshop-downloads-initialization",
            "image": workshop_image,
            "imagePullPolicy": image_pull_policy,
            "securityContext": {
                "allowPrivilegeEscalation": False,
                "capabilities": {"drop": ["ALL"]},
                "runAsNonRoot": True,
                "seccompProfile": {"type": "RuntimeDefault"},
            },
            "command": ["/opt/eduk8s/sbin/setup-downloads"],
            "resources": {
                "requests": {"memory": workshop_memory},
                "limits": {"memory": workshop_memory},
            },
            "volumeMounts": [
                {"name": "assets-data", "mountPath": "/opt/assets"},
                {"name": "packages-data", "mountPath": "/opt/packages"},
                {"name": "vendir-secrets", "mountPath": "/opt/secrets"},
                {"name": "workshop-config", "mountPath": "/opt/eduk8s/config"},
            ],
        }

        deployment_body["spec"]["template"]["spec"]["initContainers"].append(
            downloads_init_container
        )

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
    additional_labels = {}

    files = workshop_spec.get("content", {}).get("files")

    if files:
        additional_env.append({"name": "DOWNLOAD_URL", "value": files})

    for name in applications.names():
        application_tag = name.upper().replace("-", "_")
        if applications.is_enabled(name):
            additional_env.append(
                {"name": "ENABLE_" + application_tag, "value": "true"}
            )
            additional_labels[
                f"training.{OPERATOR_API_GROUP}/session.applications.{name.lower()}"
            ] = "true"
        else:
            additional_env.append(
                {"name": "ENABLE_" + application_tag, "value": "false"}
            )

    # Add in extra configuration for terminal.

    if applications.is_enabled("terminal"):
        additional_env.append(
            {
                "name": "TERMINAL_LAYOUT",
                "value": applications.property("terminal", "layout", "default"),
            }
        )

    # Add in extra configuation for web console.

    if applications.is_enabled("console"):
        additional_env.append(
            {
                "name": "CONSOLE_VENDOR",
                "value": applications.property("console", "vendor", "kubernetes"),
            }
        )

        if applications.property("console", "vendor", "kubernetes") == "kubernetes":
            secret_body = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": "kubernetes-dashboard-csrf",
                    "namespace": session_namespace,
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "session",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                    },
                },
            }

            pykube.Secret(api, secret_body).create()

    # Add in extra configuration for special cases, as well as bind policy.

    resource_objects = []

    if applications.is_enabled("docker"):
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

        docker_memory = applications.property("docker", "memory", "768Mi")
        docker_storage = applications.property("docker", "storage", "5Gi")

        dockerd_image = DOCKER_IN_DOCKER_IMAGE

        dockerd_image_pull_policy = "IfNotPresent"

        if (
            dockerd_image.endswith(":main")
            or dockerd_image.endswith(":master")
            or dockerd_image.endswith(":develop")
            or dockerd_image.endswith(":latest")
            or ":" not in dockerd_image
        ):
            dockerd_image_pull_policy = "Always"

        dockerd_args = [
            "dockerd",
            "--host=unix:///var/run/workshop/docker.sock",
            f"--mtu={DOCKERD_MTU}",
        ]

        if applications.is_enabled("registry"):
            if not INGRESS_SECRET:
                dockerd_args.append(f"--insecure-registry={registry_host}")

        if DOCKERD_MIRROR_REMOTE:
            dockerd_args.extend(
                [
                    f"--insecure-registry={workshop_namespace}-mirror",
                    f"--registry-mirror=http://{workshop_namespace}-mirror:5000",
                ]
            )

        if DOCKERD_ROOTLESS:
            dockerd_args.extend(
                [
                    "--experimental",
                    "--default-runtime",
                    "crun",
                    "--add-runtime",
                    "crun=/usr/local/bin/crun",
                ]
            )

        docker_container = {
            "name": "docker",
            "image": dockerd_image,
            "imagePullPolicy": dockerd_image_pull_policy,
            "args": dockerd_args,
            "securityContext": {
                "allowPrivilegeEscalation": True,
                "capabilities": {"drop": ["KILL", "MKNOD", "SETUID", "SETGID"]},
                "seccompProfile": {"type": "RuntimeDefault"},
            },
            "resources": {
                "limits": {"memory": docker_memory},
                "requests": {"memory": docker_memory},
            },
            "volumeMounts": [
                {
                    "name": "docker-socket",
                    "mountPath": "/var/run/workshop",
                },
            ],
        }

        if DOCKERD_ROOTLESS:
            docker_container["volumeMounts"].append(
                {
                    "name": "docker-data",
                    "mountPath": "/home/rootless/.local/share/docker",
                    "subPath": "data",
                }
            )

            docker_init_container = {
                "name": "docker-init",
                "image": dockerd_image,
                "imagePullPolicy": dockerd_image_pull_policy,
                "command": ["mkdir", "-p", "/mnt/data"],
                "securityContext": {
                    "allowPrivilegeEscalation": False,
                    "capabilities": {"drop": ["ALL"]},
                    "runAsNonRoot": True,
                    "runAsUser": 1000,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "resources": {
                    "limits": {"memory": docker_memory},
                    "requests": {"memory": docker_memory},
                },
                "volumeMounts": [
                    {
                        "name": "docker-data",
                        "mountPath": "/mnt",
                    }
                ],
            }

            deployment_body["spec"]["template"]["spec"]["initContainers"].append(
                docker_init_container
            )

            docker_security_context = {
                "allowPrivilegeEscalation": False,
                "privileged": False,
                "runAsUser": 1000,
            }

            if DOCKERD_PRIVILEGED:
                docker_security_context["allowPrivilegeEscalation"] = True
                docker_security_context["privileged"] = True

            deployment_body["spec"]["template"]["spec"]["securityContext"][
                "supplementalGroups"
            ].append(1000)

        else:
            docker_container["volumeMounts"].append(
                {"name": "docker-data", "mountPath": "/var/lib/docker"}
            )

            docker_security_context = {
                "allowPrivilegeEscalation": True,
                "privileged": True,
                "runAsUser": 0,
            }

        docker_container["securityContext"].update(docker_security_context)

        deployment_body["spec"]["template"]["spec"]["containers"].append(
            docker_container
        )

        deployment_body["metadata"]["labels"].update(
            {f"training.{OPERATOR_API_GROUP}/session.services.docker": "true"}
        )
        deployment_body["spec"]["template"]["metadata"]["labels"].update(
            {f"training.{OPERATOR_API_GROUP}/session.services.docker": "true"}
        )

        resource_objects = [
            {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {
                    "name": f"{session_namespace}-docker",
                    "namespace": workshop_namespace,
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "session",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                    },
                },
                "spec": {
                    "accessModes": [
                        "ReadWriteOnce",
                    ],
                    "resources": {
                        "requests": {
                            "storage": docker_storage,
                        }
                    },
                },
            },
        ]

        if CLUSTER_STORAGE_CLASS:
            resource_objects[0]["spec"]["storageClassName"] = CLUSTER_STORAGE_CLASS

    for object_body in resource_objects:
        object_body = _substitute_variables(object_body)
        kopf.adopt(object_body)
        create_from_dict(object_body)

    # Add in extra configuration for registry and create session objects.

    if applications.is_enabled("registry"):
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
                "value": registry_host,
            }
        )
        additional_env.append(
            {
                "name": "REGISTRY_USERNAME",
                "value": registry_username,
            }
        )
        additional_env.append(
            {
                "name": "REGISTRY_PASSWORD",
                "value": registry_password,
            }
        )
        additional_env.append(
            {
                "name": "REGISTRY_SECRET",
                "value": registry_secret,
            }
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
            {
                "name": "registry",
                "mountPath": "/var/run/registry",
            },
        ]

        deployment_body["spec"]["template"]["spec"]["containers"][0][
            "volumeMounts"
        ].extend(registry_workshop_volume_mounts)

        registry_memory = applications.property("registry", "memory", "768Mi")
        registry_storage = applications.property("registry", "storage", "5Gi")

        registry_config = {"auths": {registry_host: {"auth": f"{registry_basic_auth}"}}}

        registry_persistent_volume_claim_body = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": registry_storage}},
            },
        }

        if CLUSTER_STORAGE_CLASS:
            registry_persistent_volume_claim_body["spec"][
                "storageClassName"
            ] = CLUSTER_STORAGE_CLASS

        registry_config_map_body = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "data": {
                "htpasswd": registry_htpasswd,
                "config.json": json.dumps(registry_config, indent=4),
            },
        }

        registry_image = DOCKER_REGISTRY_IMAGE

        registry_image_pull_policy = "IfNotPresent"

        if (
            registry_image.endswith(":main")
            or registry_image.endswith(":master")
            or registry_image.endswith(":develop")
            or registry_image.endswith(":latest")
            or ":" not in registry_image
        ):
            registry_image_pull_policy = "Always"

        registry_deployment_body = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                    f"training.{OPERATOR_API_GROUP}/session.services.registry": "true",
                },
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {"deployment": f"{session_namespace}-registry"}
                },
                "strategy": {"type": "Recreate"},
                "template": {
                    "metadata": {
                        "labels": {
                            "deployment": f"{session_namespace}-registry",
                            f"training.{OPERATOR_API_GROUP}/component": "session",
                            f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                            f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                            f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                            f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                            f"training.{OPERATOR_API_GROUP}/session.services.registry": "true",
                        },
                    },
                    "spec": {
                        "serviceAccountName": f"{OPERATOR_NAME_PREFIX}-services",
                        "initContainers": [],
                        "containers": [
                            {
                                "name": "registry",
                                "image": registry_image,
                                "imagePullPolicy": registry_image_pull_policy,
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "capabilities": {"drop": ["ALL"]},
                                    "runAsNonRoot": True,
                                    "seccompProfile": {"type": "RuntimeDefault"},
                                },
                                "resources": {
                                    "limits": {"memory": registry_memory},
                                    "requests": {"memory": registry_memory},
                                },
                                "ports": [{"containerPort": 5000, "protocol": "TCP"}],
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
                        "securityContext": {
                            "runAsUser": 1000,
                            "fsGroup": CLUSTER_STORAGE_GROUP,
                            "supplementalGroups": [CLUSTER_STORAGE_GROUP],
                        },
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
                                    "items": [{"key": "htpasswd", "path": "htpasswd"}],
                                },
                            },
                        ],
                    },
                },
            },
        }

        if CLUSTER_STORAGE_USER:
            # This hack is to cope with Kubernetes clusters which don't
            # properly set up persistent volume ownership. IBM
            # Kubernetes is one example. The init container runs as root
            # and sets permissions on the storage and ensures it is
            # group writable. Note that this will only work where pod
            # security policies are not enforced. Don't attempt to use
            # it if they are. If they are, this hack should not be
            # required.

            storage_init_container = {
                "name": "storage-permissions-initialization",
                "image": registry_image,
                "imagePullPolicy": registry_image_pull_policy,
                "securityContext": {
                    "allowPrivilegeEscalation": False,
                    "capabilities": {"drop": ["ALL"]},
                    "runAsNonRoot": False,
                    "runAsUser": 0,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "command": ["/bin/sh", "-c"],
                "args": [
                    f"chown {CLUSTER_STORAGE_USER}:{CLUSTER_STORAGE_GROUP} /mnt && chmod og+rwx /mnt"
                ],
                "resources": {
                    "limits": {"memory": registry_memory},
                    "requests": {"memory": registry_memory},
                },
                "volumeMounts": [{"name": "data", "mountPath": "/mnt"}],
            }

            registry_deployment_body["spec"]["template"]["spec"][
                "initContainers"
            ].append(storage_init_container)

        registry_service_body = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [{"port": 5000, "targetPort": 5000}],
                "selector": {"deployment": f"{session_namespace}-registry"},
            },
        }

        registry_ingress_body = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "annotations": {"nginx.ingress.kubernetes.io/proxy-body-size": "512m"},
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "session",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                },
            },
            "spec": {
                "rules": [
                    {
                        "host": registry_host,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": f"{session_namespace}-registry",
                                            "port": {"number": 5000},
                                        }
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
        }

        if INGRESS_PROTOCOL == "https":
            registry_ingress_body["metadata"]["annotations"].update(
                {
                    "ingress.kubernetes.io/force-ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
                }
            )

        if INGRESS_SECRET:
            registry_ingress_body["spec"]["tls"] = [
                {
                    "hosts": [registry_host],
                    "secretName": INGRESS_SECRET,
                }
            ]

        registry_objects = [
            registry_persistent_volume_claim_body,
            registry_config_map_body,
            registry_deployment_body,
            registry_service_body,
            registry_ingress_body,
        ]

        for object_body in registry_objects:
            object_body = _substitute_variables(object_body)
            kopf.adopt(object_body)
            create_from_dict(object_body)

    if applications.is_enabled("git"):
        additional_env.append(
            {
                "name": "GIT_PROTOCOL",
                "value": INGRESS_PROTOCOL,
            }
        )
        additional_env.append(
            {
                "name": "GIT_HOST",
                "value": git_host,
            }
        )
        additional_env.append(
            {
                "name": "GIT_USERNAME",
                "value": git_username,
            }
        )
        additional_env.append(
            {
                "name": "GIT_PASSWORD",
                "value": git_password,
            }
        )

    # Apply any additional environment variables to the deployment.

    _apply_environment_patch(additional_env)

    # Overlay any additional labels to the deployment.

    deployment_body["metadata"]["labels"].update(additional_labels)
    deployment_body["spec"]["template"]["metadata"]["labels"].update(additional_labels)

    # Create a service so that the workshop environment can be accessed.
    # This is only internal to the cluster, so port forwarding or an
    # ingress is still needed to access it from outside of the cluster.

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": session_namespace,
            "namespace": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            },
        },
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

    # Create the ingress for the workshop, including any for extra named
    # named ingresses.

    ingress_rules = [
        {
            "host": session_hostname,
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": session_namespace,
                                "port": {"number": 10080},
                            }
                        },
                    }
                ]
            },
        }
    ]

    ingresses = []
    ingress_hostnames = []

    if workshop_spec.get("session"):
        ingresses = workshop_spec["session"].get("ingresses", [])

    if applications.is_enabled("console"):
        ingress_hostnames.append(f"console-{session_namespace}.{INGRESS_DOMAIN}")
        # Suffix use is deprecated. See prior note.
        ingress_hostnames.append(f"{session_namespace}-console.{INGRESS_DOMAIN}")
    if applications.is_enabled("editor"):
        ingress_hostnames.append(f"editor-{session_namespace}.{INGRESS_DOMAIN}")
        # Suffix use is deprecated. See prior note.
        ingress_hostnames.append(f"{session_namespace}-editor.{INGRESS_DOMAIN}")

    if applications.is_enabled("git"):
        ingresses.append(
            {"name": "git", "port": 10087, "authentication": {"type": "none"}}
        )

        ingress_hostnames.append(f"git-{session_namespace}.{INGRESS_DOMAIN}")
        # Suffix use is deprecated. See prior note.
        ingress_hostnames.append(f"{session_namespace}-git.{INGRESS_DOMAIN}")

    for ingress in ingresses:
        ingress_hostnames.append(
            f"{ingress['name']}-{session_namespace}.{INGRESS_DOMAIN}"
        )
        # Suffix use is deprecated. See prior note.
        ingress_hostnames.append(
            f"{session_namespace}-{ingress['name']}.{INGRESS_DOMAIN}"
        )

    for ingress_hostname in ingress_hostnames:
        ingress_rules.append(
            {
                "host": ingress_hostname,
                "http": {
                    "paths": [
                        {
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": session_namespace,
                                    "port": {"number": 10080},
                                }
                            },
                        }
                    ]
                },
            }
        )

    ingress_body = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": session_namespace,
            "namespace": workshop_namespace,
            "annotations": {
                "nginx.ingress.kubernetes.io/enable-cors": "true",
                "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600",
                "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
                "projectcontour.io/websocket-routes": "/",
                "projectcontour.io/response-timeout": "3600s",
            },
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "session",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
            },
        },
        "spec": {
            "rules": ingress_rules,
        },
    }

    if INGRESS_PROTOCOL == "https":
        ingress_body["metadata"]["annotations"].update(
            {
                "ingress.kubernetes.io/force-ssl-redirect": "true",
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
            }
        )

    if INGRESS_SECRET:
        ingress_body["spec"]["tls"] = [
            {
                "hosts": [session_hostname] + ingress_hostnames,
                "secretName": INGRESS_SECRET,
            }
        ]

    if INGRESS_CLASS:
        ingress_body["metadata"]["annotations"][
            "kubernetes.io/ingress.class"
        ] = INGRESS_CLASS

    # Update deployment with host aliases for the ports which ingresses are
    # targeting. This is so thay can be accessed by hostname rather than by
    # localhost. If follow convention of accessing by hostname then can be
    # compatible if workshop deployed with docker-compose. Note that originally
    # was using suffixes for the ingress name but switched to a prefix as DNS
    # resolvers like nip.io support a prefix on a hostname consisting of an IP
    # address which could also be useful when using docker-compose.

    host_aliases = [
        {
            "ip": "127.0.0.1",
            "hostnames": [
                f"console-{session_namespace}",
                f"editor-{session_namespace}",
                # Suffix use is deprecated. See prior note.
                f"{session_namespace}-console",
                f"{session_namespace}-editor",
            ],
        }
    ]

    for ingress in ingresses:
        host_aliases[0]["hostnames"].append(f"{ingress['name']}-{session_namespace}")
        # Suffix use is deprecated. See prior note.
        host_aliases[0]["hostnames"].append(f"{session_namespace}-{ingress['name']}")

    deployment_body["spec"]["template"]["spec"]["hostAliases"].extend(host_aliases)

    # Finally create the deployment, service and ingress for the workshop
    # session.

    kopf.adopt(deployment_body)

    pykube.Deployment(api, deployment_body).create()

    kopf.adopt(service_body)

    pykube.Service(api, service_body).create()

    kopf.adopt(ingress_body)

    pykube.Ingress(api, ingress_body).create()

    # Set the URL for accessing the workshop session directly in the
    # status. This would only be used if directly creating workshop
    # session and not when using training portal. Set phase to Running
    # if standalone workshop environment or Available if associated
    # with a training portal. The latter can be overridden though if
    # the training portal had already set the phase before the operator
    # had managed to process the resource.

    url = f"{INGRESS_PROTOCOL}://{session_hostname}"

    phase = "Running"

    if portal_name:
        phase = status.get(OPERATOR_STATUS_KEY, {}).get("phase", "Available")

    return {"phase": phase, "url": url}


@kopf.on.delete(
    f"training.{OPERATOR_API_GROUP}", "v1beta1", "workshopsessions", optional=True
)
def workshop_session_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
