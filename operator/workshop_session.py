import os
import time
import random
import string
import base64
import json
import copy

import bcrypt

import kopf
import pykube

from system_profile import (
    operator_ingress_domain,
    operator_ingress_protocol,
    operator_ingress_secret,
    operator_ingress_class,
    operator_storage_class,
    operator_storage_user,
    operator_storage_group,
    operator_dockerd_mtu,
    operator_dockerd_mirror_remote,
    operator_dockerd_rootless,
    operator_dockerd_privileged,
    environment_image_pull_secrets,
    workshop_container_image,
    registry_image_pull_secret,
    analytics_google_tracking_id,
)

from objects import create_from_dict
from helpers import Applications

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
    ingress_protocol,
    ingress_domain,
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
):
    # When a namespace is created, it needs to be populated with the default
    # service account, as well as potentially resource quotas and limit
    # ranges. If those aren't created immediately, some of the following steps
    # mail fail. At least try to wait for the default service account to be
    # created as it must always exist. Others are more problematic since they
    # may or may not exist.

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

    # Delete any limit ranges applied to the namespace that may conflict
    # with the limit range being applied. For the case of custom, we
    # delete any being applied but don't replace it. It is assumed that
    # the session objects for the workshop will define any limit ranges
    # and resource quotas itself.

    if budget != "default":
        for limit_range in pykube.LimitRange.objects(api, namespace=target_namespace).all():
            try:
                limit_range.delete()
            except pykube.exceptions.ObjectDoesNotExist:
                pass

    # Delete any resource quotas applied to the namespace that may
    # conflict with the resource quotas being applied.

    if budget != "default":
        for resource_quota in pykube.ResourceQuota.objects(api, namespace=target_namespace).all():
            try:
                resource_quota.delete()
            except pykube.exceptions.ObjectDoesNotExist:
                pass

    # Create role binding in the namespace so the service account under
    # which the workshop environment runs can create resources in it.

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": "eduk8s",
            "namespace": target_namespace,
            "labels": {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            },
        },
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

    pykube.RoleBinding(api, role_binding_body).create()

    # Create rolebinding so that all service accounts in the namespace
    # are bound by the default pod security policy.

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": "eduk8s-policy",
            "namespace": target_namespace,
            "labels": {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{workshop_namespace}-default",
        },
        "subjects": [
            {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Group",
                "name": f"system:serviceaccounts:{target_namespace}",
            }
        ],
    }

    pykube.RoleBinding(api, role_binding_body).create()

    # Create secret which holds image registry '.docker/config.json' and
    # apply it to the default service account in the target namespace so
    # that any deployment using that service account can pull images
    # from the image registry without needing to explicitly add their
    # own image pull secret.

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
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
                },
            },
            "type": "kubernetes.io/dockerconfigjson",
            "stringData": {".dockerconfigjson": json.dumps(registry_config, indent=4)},
        }

        pykube.Secret(api, secret_body).create()

        # The service account needs to have been created at this point or this
        # will fail. This is because we need to patch it with the image pull
        # secrets.

        service_account_instance = pykube.ServiceAccount.objects(
            api, namespace=target_namespace
        ).get(name="default")

        image_pull_secrets = service_account_instance.obj.get("imagePullSecrets", [])

        if {"name": registry_secret} not in image_pull_secrets:
            image_pull_secrets.append({"name": registry_secret})

        service_account_instance.obj["imagePullSecrets"] = image_pull_secrets

        service_account_instance.update()

        # image_pull_secrets = service_account_instance.obj.get("imagePullSecrets" or []
        # image_pull_secrets.append({"name": registry_secret})

        # service_account_patch = [
        #     {"op": "replace", "path": "/imagePullSecrets", "value": image_pull_secrets}
        # ]

        # core_api.patch_namespaced_service_account(
        #     namespace=target_namespace, name="default", body=service_account_patch
        # )

    # Create limit ranges for the namespace so any deployments will have
    # default memory/cpu min and max values.

    if budget not in ("default", "custom"):
        resource_limits_body = copy.deepcopy(resource_limits_definition)

        resource_limits_body["metadata"].setdefault("labels", {}).update(
            {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            }
        )

        resource_limits_body["metadata"]["namespace"] = target_namespace

        pykube.LimitRange(api, resource_limits_body).create()

    # Create resource quotas for the namespace so there is a maximum for
    # what resources can be used.

    if budget not in ("default", "custom"):
        resource_quota_body = copy.deepcopy(compute_resources_definition)

        resource_quota_body["metadata"].setdefault("labels", {}).update(
            {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            }
        )

        resource_quota_body["metadata"]["namespace"] = target_namespace

        pykube.ResourceQuota(api, resource_quota_body).create()

        resource_quota_body = copy.deepcopy(compute_resources_timebound_definition)

        resource_quota_body["metadata"].setdefault("labels", {}).update(
            {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            }
        )

        resource_quota_body["metadata"]["namespace"] = target_namespace

        pykube.ResourceQuota(api, resource_quota_body).create()

        resource_quota_body = copy.deepcopy(object_counts_definition)

        resource_quota_body["metadata"].setdefault("labels", {}).update(
            {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            }
        )

        resource_quota_body["metadata"]["namespace"] = target_namespace

        pykube.ResourceQuota(api, resource_quota_body).create()

        # Verify that the status of the resource quotas have been
        # updated. If we don't do this, then the calculated hard limits
        # may not be calculated before we start creating resources in
        # the namespace resulting in a failure. If we can't manage to
        # verify quotas after a period, give up. This may result in a
        # subsequent failure.

        for _ in range(25):
            resource_quotas = pykube.ResourceQuota.objects(api, namespace=target_namespace).all()

            for resource_quota in resource_quotas:
                if not resource_quota.obj.get("status") or not resource_quota.obj["status"].get("hard"):
                    time.sleep(0.1)
                    continue

            break


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshopsessions", id="eduk8s")
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

    K8SWorkshopEnvironment = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopEnvironment"
    )

    try:
        environment_instance = K8SWorkshopEnvironment.objects(api).get(
            name=workshop_namespace
        )

    except pykube.exceptions.ObjectDoesNotExist:
        patch["status"] = {"eduk8s": {"phase": "Pending"}}
        raise kopf.TemporaryError(f"Environment {workshop_namespace} does not exist.")

    session_id = spec["session"]["id"]
    session_namespace = f"{workshop_namespace}-{session_id}"

    # Can optionally be passed name of the training portal via a label
    # when the workshop environment is created as a child to a training
    # portal.

    portal_name = meta.get("labels", {}).get("training.eduk8s.io/portal.name", "")

    # We pull details of the workshop to be deployed from the status of
    # the workspace custom resource. This is a copy of the specification
    # from the custom resource for the workshop. We use a copy so we
    # aren't affected by changes in the original workshop made after the
    # workspace was created.

    if not environment_instance.obj.get("status") or not environment_instance.obj[
        "status"
    ].get("eduk8s"):
        patch["status"] = {"eduk8s": {"phase": "Pending"}}
        raise kopf.TemporaryError(f"Environment {workshop_namespace} is not ready.")

    workshop_name = environment_instance.obj["status"]["eduk8s"]["workshop"]["name"]
    workshop_spec = environment_instance.obj["status"]["eduk8s"]["workshop"]["spec"]

    # Create a wrapper for determining if applications enabled and what
    # configuration they provide.

    applications = Applications(workshop_spec["session"].get("applications", {}))

    # Calculate the hostname and domain being used. Need to do this so
    # we can later set the INGRESS_DOMAIN environment variable on the
    # deployment so that it is available in the workshop environment,
    # but also so we can use it replace variables in list of resource
    # objects being created.

    system_profile = spec.get("system", {}).get("profile")

    default_ingress_domain = operator_ingress_domain(system_profile)
    default_ingress_protocol = operator_ingress_protocol(system_profile)
    default_ingress_secret = operator_ingress_secret(system_profile)
    default_ingress_class = operator_ingress_class(system_profile)

    ingress_domain = (
        spec["session"].get("ingress", {}).get("domain", default_ingress_domain)
    )

    ingress_protocol = default_ingress_protocol

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
            ingress_secret_instance = pykube.Secret.objects(
                api, namespace=workshop_namespace
            ).get(name=ingress_secret)

        except pykube.exceptions.ObjectDoesNotExist:
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"TLS secret {ingress_secret} is not available for workshop."
            )

        if not ingress_secret_instance.obj["data"].get(
            "tls.crt"
        ) or not ingress_secret_instance.obj["data"].get("tls.key"):
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"TLS secret {ingress_secret} for workshop is not valid."
            )

        ingress_protocol = "https"

    # Calculate a random password for the image registry if required.

    if applications.is_enabled("registry"):
        characters = string.ascii_letters + string.digits

        registry_host = f"{session_namespace}-registry.{ingress_domain}"
        registry_username = session_namespace
        registry_password = "".join(random.sample(characters, 32))
        registry_secret = "eduk8s-registry-credentials"

        applications.properties("registry")["host"] = registry_host
        applications.properties("registry")["username"] = registry_username
        applications.properties("registry")["password"] = registry_password
        applications.properties("registry")["secret"] = registry_secret

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
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            },
        },
    }

    kopf.adopt(namespace_body)

    try:
        pykube.Namespace(api, namespace_body).create()

    except pykube.exceptions.PyKubeError as e:
        if e.code == 409:
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
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

    image_pull_secrets = list(environment_image_pull_secrets(system_profile))

    pull_secret_name = registry_image_pull_secret(system_profile)

    if pull_secret_name and pull_secret_name not in image_pull_secrets:
        image_pull_secrets.append(pull_secret_name)

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": service_account,
            "namespace": workshop_namespace,
            "labels": {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            },
        },
        "imagePullSecrets": [
            {"name": pull_secret_name} for pull_secret_name in image_pull_secrets
        ],
    }

    kopf.adopt(service_account_body)

    pykube.ServiceAccount(api, service_account_body).create()

    # Create the rolebinding for this service account to add access to
    # the additional roles that the Kubernetes web console requires.

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": f"{session_namespace}-console",
            "labels": {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            },
        },
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

    pykube.ClusterRoleBinding(api, cluster_role_binding_body).create()

    # Setup configuration on the primary session namespace.

    role = "admin"
    budget = "default"
    limits = {}
    security_policy = "default"

    if workshop_spec.get("session"):
        # Use of "session.role" and "session.budget" is deprecated and
        # will be removed in next custom resource version updated. Use
        # "session.namespaces.role" and "session.namespaces.budget".

        role = workshop_spec["session"].get("role", role)
        budget = workshop_spec["session"].get("budget", budget)

        role = workshop_spec["session"].get("namespaces", {}).get("role", role)
        budget = workshop_spec["session"].get("namespaces", {}).get("budget", budget)
        limits = workshop_spec["session"].get("namespaces", {}).get("limits", limits)

        security_policy = (
            workshop_spec["session"].get("security", {}).get("policy", security_policy)
        )

    _setup_session_namespace(
        ingress_protocol,
        ingress_domain,
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
    )

    # Claim a persistent volume for the workshop session if requested.

    storage = workshop_spec.get("session", {}).get("resources", {}).get("storage")

    default_storage_class = operator_storage_class(system_profile)
    default_storage_user = operator_storage_user(system_profile)
    default_storage_group = operator_storage_group(system_profile)

    if storage:
        persistent_volume_claim_body = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{session_namespace}",
                "namespace": workshop_namespace,
                "labels": {
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
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

        if default_storage_class:
            persistent_volume_claim_body["spec"][
                "storageClassName"
            ] = default_storage_class

        kopf.adopt(persistent_volume_claim_body)

        pykube.PersistentVolumeClaim(api, persistent_volume_claim_body).create()

    # Helper function to replace variables in values for objects etc.

    def _substitute_variables(obj):
        if isinstance(obj, str):
            obj = obj.replace("$(session_id)", session_id)
            obj = obj.replace("$(session_namespace)", session_namespace)
            obj = obj.replace("$(service_account)", service_account)
            obj = obj.replace("$(environment_name)", environment_name)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            obj = obj.replace("$(ingress_domain)", ingress_domain)
            obj = obj.replace("$(ingress_protocol)", ingress_protocol)
            obj = obj.replace("$(ingress_port_suffix)", "")
            obj = obj.replace("$(ingress_secret)", ingress_secret)
            if applications.is_enabled("registry"):
                obj = obj.replace("$(registry_host)", registry_host)
                obj = obj.replace("$(registry_username)", registry_username)
                obj = obj.replace("$(registry_password)", registry_password)
                obj = obj.replace("$(registry_secret)", registry_secret)
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

            namespace_body = {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": target_namespace,
                    "labels": {
                        "training.eduk8s.io/component": "session",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
                        "training.eduk8s.io/session.name": session_name,
                    },
                },
            }

            kopf.adopt(namespace_body)

            try:
                pykube.Namespace(api, namespace_body).create()

            except pykube.exceptions.PyKubeError as e:
                if e.code == 409:
                    patch["status"] = {"eduk8s": {"phase": "Pending"}}
                    raise kopf.TemporaryError(
                        f"Namespace {target_namespace} already exists."
                    )
                raise

            target_role = namespaces_item.get("role", role)
            target_budget = namespaces_item.get("budget", budget)
            target_limits = namespaces_item.get("limits", {})

            _setup_session_namespace(
                ingress_protocol,
                ingress_domain,
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
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
                "training.eduk8s.io/session.objects": "true",
            }
        )

        kopf.adopt(object_body)

        create_from_dict(object_body)

        if api_version == "v1" and kind.lower() == "namespace":
            annotations = object_body["metadata"].get("annotations", {})

            target_role = annotations.get("training.eduk8s.io/session.role", role)
            target_budget = annotations.get("training.eduk8s.io/session.budget", budget)
            target_limits = {}

            if annotations.get("training.eduk8s.io/session.limits.min.cpu"):
                target_limits.setdefault("min", {})["cpu"] = annotations[
                    "training.eduk8s.io/session.limits.min.cpu"
                ]
            if annotations.get("training.eduk8s.io/session.limits.min.memory"):
                target_limits.setdefault("min", {})["memory"] = annotations[
                    "training.eduk8s.io/session.limits.min.memory"
                ]

            if annotations.get("training.eduk8s.io/session.limits.max.cpu"):
                target_limits.setdefault("max", {})["cpu"] = annotations[
                    "training.eduk8s.io/session.limits.max.cpu"
                ]
            if annotations.get("training.eduk8s.io/session.limits.max.memory"):
                target_limits.setdefault("max", {})["memory"] = annotations[
                    "training.eduk8s.io/session.limits.max.memory"
                ]

            if annotations.get("training.eduk8s.io/session.limits.defaultrequest.cpu"):
                target_limits.setdefault("defaultRequest", {})["cpu"] = annotations[
                    "training.eduk8s.io/session.limits.defaultrequest.cpu"
                ]
            if annotations.get(
                "training.eduk8s.io/session.limits.defaultrequest.memory"
            ):
                target_limits.setdefault("defaultRequest", {})["memory"] = annotations[
                    "training.eduk8s.io/session.limits.defaultrequest.memory"
                ]

            if annotations.get("training.eduk8s.io/session.limits.default.cpu"):
                target_limits.setdefault("default", {})["cpu"] = annotations[
                    "training.eduk8s.io/session.limits.default.cpu"
                ]
            if annotations.get("training.eduk8s.io/session.limits.default.memory"):
                target_limits.setdefault("default", {})["memory"] = annotations[
                    "training.eduk8s.io/session.limits.default.memory"
                ]

            target_namespace = object_body["metadata"]["name"]

            _setup_session_namespace(
                ingress_protocol,
                ingress_domain,
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
            )

        elif api_version == "v1" and kind.lower() == "resourcequota":
            # Verify that the status of the resource quota has been
            # updated. If we don't do this, then the calculated hard
            # limits may not be calculated before we start creating
            # resources in the namespace resulting in a failure. If we
            # can't manage to verify quotas after a period, give up.
            # This may result in a subsequent failure.

            for _ in range(25):
                resource_quota = core_api.read_namespaced_resource_quota(
                    object_body["metadata"]["name"],
                    namespace=object_body["metadata"]["namespace"],
                )

                if not resource_quota.status or not resource_quota.status.hard:
                    time.sleep(0.1)
                    continue

    # Next setup the deployment resource for the workshop dashboard.

    username = spec["session"].get("username", "")
    password = spec["session"].get("password", "")

    workshop_image = workshop_container_image(
        workshop_spec.get("content", {}).get("image"), system_profile
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

    google_tracking_id = analytics_google_tracking_id(system_profile)

    google_tracking_id = (
        spec.get("analytics", {})
        .get("google", {})
        .get("trackingId", google_tracking_id)
    )

    if (
        workshop_image.endswith(":master")
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
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
                "training.eduk8s.io/session.services.workshop": "true",
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
                        "training.eduk8s.io/component": "session",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
                        "training.eduk8s.io/session.name": session_name,
                        "training.eduk8s.io/session.services.workshop": "true",
                    },
                },
                "spec": {
                    "serviceAccountName": service_account,
                    "securityContext": {
                        "fsGroup": default_storage_group,
                        "supplementalGroups": [default_storage_group],
                    },
                    "initContainers": [],
                    "containers": [
                        {
                            "name": "workshop",
                            "image": workshop_image,
                            "imagePullPolicy": image_pull_policy,
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
                                    "name": "AUTH_USERNAME",
                                    "value": username,
                                },
                                {
                                    "name": "AUTH_PASSWORD",
                                    "value": password,
                                },
                                {
                                    "name": "INGRESS_DOMAIN",
                                    "value": ingress_domain,
                                },
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

        if default_storage_user:
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
                "image": workshop_image,
                "imagePullPolicy": image_pull_policy,
                "securityContext": {"runAsUser": 0},
                "command": ["/bin/sh", "-c"],
                "args": [
                    f"chown {default_storage_user}:{default_storage_group} /mnt && chmod og+rwx /mnt"
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
        if applications.is_enabled(name):
            additional_env.append({"name": "ENABLE_" + name.upper(), "value": "true"})
            additional_labels[
                f"training.eduk8s.io/session.applications.{name.lower()}"
            ] = "true"
        else:
            additional_env.append({"name": "ENABLE_" + name.upper(), "value": "false"})

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
                        "training.eduk8s.io/component": "session",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
                        "training.eduk8s.io/session.name": session_name,
                    },
                },
            }

            pykube.Secret(api, secret_body).create()

        if applications.property("console", "vendor") == "openshift":
            console_version = applications.property(
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

            deployment_body["metadata"]["labels"].update(
                {"training.eduk8s.io/session.services.openshift": "true"}
            )
            deployment_body["spec"]["template"]["metadata"]["labels"].update(
                {"training.eduk8s.io/session.services.openshift": "true"}
            )

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

        default_dockerd_mtu = operator_dockerd_mtu(system_profile)
        default_dockerd_mirror_remote = operator_dockerd_mirror_remote(system_profile)

        default_dockerd_rootless = operator_dockerd_rootless(system_profile)
        default_dockerd_privileged = operator_dockerd_privileged(system_profile)

        # Use same rootless enabled image in both cases. This image has
        # symlink for /var/run/docker.sock. Not believed at this point
        # that using rootless enabled image will cause issues when run
        # as root rather than rootless.

        # if default_dockerd_rootless:
        #    docker_dind_image = (
        #        "quay.io/eduk8s/eduk8s-dind-rootless:201105.032145.5dfb9e6"
        #    )
        # else:
        #    docker_dind_image = "docker:19.03-dind"

        docker_dind_image = "quay.io/eduk8s/eduk8s-dind-rootless:201105.032145.5dfb9e6"

        dockerd_args = [
            "dockerd",
            "--host=unix:///var/run/workshop/docker.sock",
            f"--mtu={default_dockerd_mtu}",
        ]

        if applications.is_enabled("registry"):
            if not ingress_secret:
                dockerd_args.append(f"--insecure-registry={registry_host}")

        if default_dockerd_mirror_remote:
            dockerd_args.extend(
                [
                    f"--insecure-registry={workshop_namespace}-mirror",
                    f"--registry-mirror=http://{workshop_namespace}-mirror:5000",
                ]
            )

        if default_dockerd_rootless:
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
            "image": docker_dind_image,
            "args": dockerd_args,
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

        if default_dockerd_rootless:
            docker_container["volumeMounts"].append(
                {
                    "name": "docker-data",
                    "mountPath": "/home/rootless/.local/share/docker",
                    "subPath": "data",
                }
            )

            docker_init_container = {
                "name": "docker-init",
                "image": docker_dind_image,
                "command": ["mkdir", "/mnt/data"],
                "securityContext": {"runAsUser": 1000},
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

            docker_security_context = {"runAsUser": 1000}

            if default_dockerd_privileged:
                docker_security_context["privileged"] = True

            deployment_body["spec"]["template"]["spec"]["securityContext"][
                "supplementalGroups"
            ].append(1000)

        else:
            docker_container["volumeMounts"].append(
                {"name": "docker-data", "mountPath": "/var/lib/docker"}
            )

            docker_security_context = {"privileged": True, "runAsUser": 0}

        docker_container["securityContext"] = docker_security_context

        deployment_body["spec"]["template"]["spec"]["containers"].append(
            docker_container
        )

        deployment_body["metadata"]["labels"].update(
            {"training.eduk8s.io/session.services.docker": "true"}
        )
        deployment_body["spec"]["template"]["metadata"]["labels"].update(
            {"training.eduk8s.io/session.services.docker": "true"}
        )

        resource_objects = [
            {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {
                    "name": f"{session_namespace}-docker",
                    "namespace": workshop_namespace,
                    "labels": {
                        "training.eduk8s.io/component": "session",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
                        "training.eduk8s.io/session.name": session_name,
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

        if default_storage_class:
            resource_objects[0]["spec"]["storageClassName"] = default_storage_class

    if security_policy != "custom":
        if applications.is_enabled("docker"):
            resource_objects.extend(
                [
                    {
                        "apiVersion": "rbac.authorization.k8s.io/v1",
                        "kind": "RoleBinding",
                        "metadata": {
                            "name": f"{session_namespace}-docker",
                            "namespace": workshop_namespace,
                            "labels": {
                                "training.eduk8s.io/component": "session",
                                "training.eduk8s.io/workshop.name": workshop_name,
                                "training.eduk8s.io/portal.name": portal_name,
                                "training.eduk8s.io/environment.name": environment_name,
                                "training.eduk8s.io/session.name": session_name,
                            },
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
                            "name": f"{session_namespace}-default",
                            "namespace": workshop_namespace,
                            "labels": {
                                "training.eduk8s.io/component": "session",
                                "training.eduk8s.io/workshop.name": workshop_name,
                                "training.eduk8s.io/portal.name": portal_name,
                                "training.eduk8s.io/environment.name": environment_name,
                                "training.eduk8s.io/session.name": session_name,
                            },
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
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
                },
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": registry_storage}},
            },
        }

        if default_storage_class:
            registry_persistent_volume_claim_body["spec"][
                "storageClassName"
            ] = default_storage_class

        registry_config_map_body = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "labels": {
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
                },
            },
            "data": {
                "htpasswd": registry_htpasswd,
                "config.json": json.dumps(registry_config, indent=4),
            },
        }

        registry_deployment_body = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "labels": {
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
                    "training.eduk8s.io/session.services.registry": "true",
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
                            "training.eduk8s.io/component": "session",
                            "training.eduk8s.io/workshop.name": workshop_name,
                            "training.eduk8s.io/portal.name": portal_name,
                            "training.eduk8s.io/environment.name": environment_name,
                            "training.eduk8s.io/session.name": session_name,
                            "training.eduk8s.io/session.services.registry": "true",
                        },
                    },
                    "spec": {
                        "serviceAccountName": "eduk8s-services",
                        "initContainers": [],
                        "containers": [
                            {
                                "name": "registry",
                                "image": "registry.hub.docker.com/library/registry:2.6.1",
                                "imagePullPolicy": "IfNotPresent",
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
                            "fsGroup": default_storage_group,
                            "supplementalGroups": [default_storage_group],
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

        if default_storage_user:
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
                "image": "registry.hub.docker.com/library/registry:2.6.1",
                "imagePullPolicy": "IfNotPresent",
                "securityContext": {"runAsUser": 0},
                "command": ["/bin/sh", "-c"],
                "args": [
                    f"chown {default_storage_user}:{default_storage_group} /mnt && chmod og+rwx /mnt"
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
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
                },
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [{"port": 5000, "targetPort": 5000}],
                "selector": {"deployment": f"{session_namespace}-registry"},
            },
        }

        registry_ingress_body = {
            "apiVersion": "networking.k8s.io/v1beta1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{session_namespace}-registry",
                "namespace": workshop_namespace,
                "annotations": {"nginx.ingress.kubernetes.io/proxy-body-size": "512m"},
                "labels": {
                    "training.eduk8s.io/component": "session",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/session.name": session_name,
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
        }

        if ingress_protocol == "https":
            registry_ingress_body["metadata"]["annotations"].update(
                {
                    "ingress.kubernetes.io/force-ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
                }
            )

        if ingress_secret:
            registry_ingress_body["spec"]["tls"] = [
                {
                    "hosts": [registry_host],
                    "secretName": ingress_secret,
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
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
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
        "apiVersion": "networking.k8s.io/v1beta1",
        "kind": "Ingress",
        "metadata": {
            "name": session_namespace,
            "namespace": workshop_namespace,
            "annotations": {
                "nginx.ingress.kubernetes.io/enable-cors": "true",
                "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600",
                "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
                "projectcontour.io/websocket-routes": "/",
                "projectcontour.io/response-timeout": "3600",
            },
            "labels": {
                "training.eduk8s.io/component": "session",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
                "training.eduk8s.io/session.name": session_name,
            },
        },
        "spec": {
            "rules": ingress_rules,
        },
    }

    if ingress_protocol == "https":
        ingress_body["metadata"]["annotations"].update(
            {
                "ingress.kubernetes.io/force-ssl-redirect": "true",
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
            }
        )

    if ingress_secret:
        ingress_body["spec"]["tls"] = [
            {
                "hosts": [session_hostname] + ingress_hostnames,
                "secretName": ingress_secret,
            }
        ]

    if ingress_class:
        ingress_body["metadata"]["annotations"][
            "kubernetes.io/ingress.class"
        ] = ingress_class

    # Update deployment with host aliases for the ports which ingresses
    # are targeting. This is so thay can be accessed by hostname rather
    # than by localhost. If follow convention of accessing by hostname
    # then can be compatible if workshop deployed with docker-compose.

    host_aliases = [
        {
            "ip": "127.0.0.1",
            "hostnames": [
                f"{session_namespace}-console",
                f"{session_namespace}-editor",
            ],
        }
    ]

    for ingress in ingresses:
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

    url = f"{ingress_protocol}://{session_hostname}"

    phase = "Running"

    if portal_name:
        phase = status.get("eduk8s", {}).get("phase", "Available")

    return {"phase": phase, "url": url}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshopsessions", optional=True)
def workshop_session_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
