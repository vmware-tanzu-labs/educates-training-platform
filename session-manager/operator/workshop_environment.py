import os
import yaml

import kopf
import pykube

from system_profile import (
    current_profile,
    active_profile_name,
    operator_ingress_domain,
    operator_ingress_protocol,
    operator_ingress_secret,
    operator_storage_class,
    operator_storage_user,
    operator_storage_group,
    operator_dockerd_mirror_remote,
    operator_dockerd_mirror_username,
    operator_dockerd_mirror_password,
    operator_network_blockcidrs,
    environment_image_pull_secrets,
    registry_image_pull_secret,
    theme_dashboard_script,
    theme_dashboard_style,
    theme_workshop_script,
    theme_workshop_style,
)

from objects import create_from_dict, Workshop
from helpers import Applications

from config import (
    OPERATOR_NAMESPACE,
    OPERATOR_API_GROUP,
    RESOURCE_STATUS_KEY,
    RESOURCE_NAME_PREFIX,
)

__all__ = ["workshop_environment_create", "workshop_environment_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "workshopenvironments",
    id=RESOURCE_STATUS_KEY,
)
def workshop_environment_create(name, meta, spec, patch, logger, **_):
    # Use the name of the custom resource as the name of the namespace
    # under which the workshop environment is created and any workshop
    # instances are created.

    environment_name = name
    workshop_namespace = environment_name

    # Can optionally be passed name of the training portal via a label
    # when the workshop environment is created as a child to a training
    # portal.

    portal_name = meta.get("labels", {}).get(
        f"training.{OPERATOR_API_GROUP}/portal.name", ""
    )

    # The name of the workshop to be deployed can differ and is taken
    # from the specification of the workspace. Lookup the workshop
    # resource definition and ensure it exists. Later we will stash a
    # copy of this in the status of the custom resource, and we will use
    # this copy to avoid being affected by changes in the original after
    # the creation of the workshop environment.

    workshop_name = spec["workshop"]["name"]

    try:
        workshop_instance = Workshop.objects(api).get(name=workshop_name)

    except pykube.exceptions.ObjectDoesNotExist:
        patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(f"Workshop {workshop_name} is not available.")

    try:
        del workshop_instance.obj["metadata"]["annotations"][
            "kubectl.kubernetes.io/last-applied-configuration"
        ]
    except KeyError:
        pass

    workshop_uid = workshop_instance.obj["metadata"]["uid"]
    workshop_generation = workshop_instance.obj["metadata"]["generation"]
    workshop_spec = workshop_instance.obj.get("spec", {})

    # Lookup what system profile should be used.

    system_profile = active_profile_name(spec.get("system", {}).get("profile"))

    system_profile_instance = current_profile(system_profile)

    if system_profile_instance is None:
        raise kopf.TemporaryError(f"System profile {system_profile} is not available.")

    # Create a wrapper for determining if applications enabled and what
    # configuration they provide.

    applications = Applications(workshop_spec["session"].get("applications", {}))

    # Create the namespace for everything related to this workshop.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "environment",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
            },
        },
    }

    # Make the namespace for the workshop a child of the custom resource
    # for the workshop environment. This way the namespace will be
    # automatically deleted when the resource definition for the
    # workshop environment is deleted and we don't have to clean up
    # anything explicitly.

    kopf.adopt(namespace_body)

    try:
        pykube.Namespace(api, namespace_body).create()

    except pykube.exceptions.PyKubeError as e:
        if e.code == 409:
            patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(f"Namespace {workshop_namespace} already exists.")
        raise

    # Delete any limit ranges applied to the namespace so they don't cause
    # issues with workshop instance deployments or any workshop deployments.
    # This can be an issue where namespace/project templates apply them
    # automatically to a namespace. The problem is that we may do this query
    # too quickly and they may not have been created as yet.

    for limit_range in pykube.LimitRange.objects(api).filter(
        namespace=workshop_namespace
    ):
        try:
            limit_range.delete()
        except pykube.exceptions.ObjectDoesNotExist:
            pass

    # Delete any resource quotas applied to the namespace so they don't cause
    # issues with workshop instance deploymemnts or any workshop resources.
    # This can be an issue where namespace/project templates apply them
    # automatically to a namespace. The problem is that we may do this query
    # too quickly and they may not have been created as yet.

    for resource_quota in pykube.ResourceQuota.objects(api).filter(
        namespace=workshop_namespace
    ):
        try:
            resource_quota.delete()
        except pykube.exceptions.ObjectDoesNotExist:
            pass

    # If the system profile specifies a CIDR list of networks to block
    # create a network policy in the workshop environment to restrict
    # access from all pods. Pods here include the workshop pods where
    # each users terminal runs.

    blockcidrs = operator_network_blockcidrs(system_profile)

    if blockcidrs:
        network_policy_body = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"{RESOURCE_NAME_PREFIX}-network-blockcidrs",
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "environment",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                },
            },
            "spec": {
                "policyTypes": ["Egress"],
                "egress": [
                    {"to": [{"ipBlock": {"cidr": "0.0.0.0/0", "except": blockcidrs}}]}
                ],
            },
        }

        kopf.adopt(network_policy_body)

        NetworkPolicy = pykube.object_factory(
            api, "networking.k8s.io/v1", "NetworkPolicy"
        )

        NetworkPolicy(api, network_policy_body).create()

    # Create a config map in the workshop namespace which contains the
    # details about the workshop. This will be mounted into workshop
    # instances so they can derive information to configure themselves.

    dashboard_js = theme_dashboard_script(system_profile)
    dashboard_css = theme_dashboard_style(system_profile)
    workshop_js = theme_workshop_script(system_profile)
    workshop_css = theme_workshop_style(system_profile)

    workshop_data = yaml.dump(workshop_instance.obj, Dumper=yaml.Dumper)

    config_map_body = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "workshop",
            "namespace": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "environment",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
            },
        },
        "data": {
            "workshop.yaml": workshop_data,
            "theme-dashboard.js": dashboard_js,
            "theme-dashboard.css": dashboard_css,
            "theme-workshop.js": workshop_js,
            "theme-workshop.css": workshop_css,
        },
    }

    kopf.adopt(config_map_body)

    pykube.ConfigMap(api, config_map_body).create()

    # Because the Kubernetes web console is designed for working against
    # a whole cluster and we want to use it in scope of a single
    # namespace, we need to at least grant it roles to be able to list
    # and get namespaces. If we don't do this then the web console will
    # forever generate a stream of events complaining that it can't read
    # namespaces. This seems to hasten the web console hanging, but also
    # means can't easily switch to other namespaces the workshop has
    # access to as the list of namespaces cannot be generated. At this
    # point we therefore create a cluster role associated with the
    # name of the namespace create for the workshop environment. This
    # will later be bound to the service account the workshop
    # instances and web consoles runs as. As with the namespace we add
    # it as a child to the custom resource for the workshop.

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": f"{workshop_namespace}-console",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "environment",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
            },
        },
        "rules": [
            {
                "apiGroups": [""],
                "resources": ["namespaces"],
                "verbs": ["get", "list", "watch"],
            }
        ],
    }

    kopf.adopt(cluster_role_body)

    pykube.ClusterRole(api, cluster_role_body).create()

    # Make a copy of the TLS secret into the workshop namespace.

    default_ingress_domain = operator_ingress_domain(system_profile)
    default_ingress_protocol = operator_ingress_protocol(system_profile)
    default_ingress_secret = operator_ingress_secret(system_profile)

    ingress_domain = (
        spec.get("session", {}).get("ingress", {}).get("domain", default_ingress_domain)
    )

    ingress_protocol = default_ingress_protocol

    if ingress_domain == default_ingress_domain:
        ingress_secret = default_ingress_secret
    else:
        ingress_secret = spec.get("session", {}).get("ingress", {}).get("secret", "")

        if ingress_secret and not "/" in ingress_secret:
            ingress_secret = f"{OPERATOR_NAMESPACE}/{ingress_secret}"

    ingress_secrets = []

    ingress_secret_name = ""

    if ingress_secret:
        ingress_secret_namespace, ingress_secret_name = ingress_secret.split("/")

        try:
            ingress_secret_instance = pykube.Secret.objects(
                api, namespace=ingress_secret_namespace
            ).get(name=ingress_secret_name)

        except pykube.exceptions.ObjectDoesNotExist:
            patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(f"TLS secret {ingress_secret} is not available.")

        if (
            ingress_secret_instance.obj["type"] != "kubernetes.io/tls"
            or not ingress_secret_instance.obj["data"].get("tls.crt")
            or not ingress_secret_instance.obj["data"].get("tls.key")
        ):
            patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(f"TLS secret {ingress_secret} is not valid.")

        ingress_protocol = "https"

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": ingress_secret_name,
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "environment",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                },
            },
            "type": "kubernetes.io/tls",
            "data": ingress_secret_instance.obj["data"],
        }

        pykube.Secret(api, secret_body).create()

        ingress_secrets.append(ingress_secret)

    # Make copies of any pull secrets into the workshop namespace.

    image_pull_secrets = list(environment_image_pull_secrets(system_profile))

    pull_secret_name = registry_image_pull_secret(system_profile)

    if pull_secret_name and pull_secret_name not in image_pull_secrets:
        image_pull_secrets.append(pull_secret_name)

    for pull_secret_name in image_pull_secrets:
        try:
            pull_secret_instance = pykube.Secret.objects(api).get(
                namespace=OPERATOR_NAMESPACE, name=pull_secret_name
            )

        except pykube.exceptions.ObjectDoesNotExist:
            patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Pull secret {pull_secret_name} is not available in namespace {OPERATOR_NAMESPACE}."
            )

        if pull_secret_instance.obj[
            "type"
        ] != "kubernetes.io/dockerconfigjson" or not pull_secret_instance.obj[
            "data"
        ].get(
            ".dockerconfigjson"
        ):
            patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(f"Pull secret {pull_secret_name} is not valid.")

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": pull_secret_name,
                "namespace": workshop_namespace,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/component": "environment",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                },
            },
            "type": "kubernetes.io/dockerconfigjson",
            "data": pull_secret_instance.obj["data"],
        }

        pykube.Secret(api, secret_body).create()

    # Create any additional resources required for the workshop, as
    # defined by the workshop resource definition and extras from the
    # workshop environment itself. Where a namespace isn't defined for a
    # namespaced resource type, the resource will be created in the
    # workshop namespace.
    #
    # XXX For now make the workshop environment resource definition the
    # parent of all objects. Technically should only do so for non
    # namespaced objects, or objects created in namespaces that already
    # existed. How to work out if a resource type is namespaced or not
    # with the Python Kubernetes client appears to be a bit of a hack.

    environment_token = spec.get("request", {}).get("token", "")

    def _substitute_variables(obj):
        if isinstance(obj, str):
            obj = obj.replace("$(workshop_name)", workshop_name)
            obj = obj.replace("$(environment_name)", environment_name)
            obj = obj.replace("$(environment_token)", environment_token)
            obj = obj.replace("$(workshop_namespace)", workshop_namespace)
            obj = obj.replace("$(service_account)", f"{RESOURCE_NAME_PREFIX}-services")
            obj = obj.replace("$(ingress_domain)", ingress_domain)
            obj = obj.replace("$(ingress_protocol)", ingress_protocol)
            obj = obj.replace("$(ingress_port_suffix)", "")
            obj = obj.replace("$(ingress_secret)", ingress_secret_name)
            return obj
        elif isinstance(obj, dict):
            return {k: _substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_variables(v) for v in obj]
        else:
            return obj

    if workshop_spec.get("environment", {}).get("objects"):
        objects = workshop_spec["environment"]["objects"]

        for object_body in objects:
            object_body = _substitute_variables(object_body)

            if not object_body["metadata"].get("namespace"):
                object_body["metadata"]["namespace"] = workshop_namespace

            object_body["metadata"].setdefault("labels", {}).update(
                {
                    f"training.{OPERATOR_API_GROUP}/component": "environment",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/environment.objects": "true",
                }
            )

            kopf.adopt(object_body)

            create_from_dict(object_body)

    if spec.get("environment", {}).get("objects"):
        objects = spec["environment"]["objects"]

        for object_body in objects:
            object_body = _substitute_variables(object_body)

            if not object_body["metadata"].get("namespace"):
                object_body["metadata"]["namespace"] = workshop_namespace

            object_body["metadata"].setdefault("labels", {}).update(
                {
                    f"training.{OPERATOR_API_GROUP}/component": "environment",
                    f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    f"training.{OPERATOR_API_GROUP}/environment.objects": "true",
                }
            )

            kopf.adopt(object_body)

            create_from_dict(object_body)

    # Set up pod security policy for workshop session. Note that a prefix of
    # "aaa-" is added to the name of the pod security policy to ensure the
    # policy takes precedence when the cluster has a default pod security
    # policy mapped to the "system:authenticated" group. If don't try and
    # ensure our name is earlier in alphabetical order, that mapped to the
    # group will take precedence.

    policy_objects = []

    if applications.is_enabled("docker"):
        policy_objects.extend(
            [
                {
                    "apiVersion": "policy/v1beta1",
                    "kind": "PodSecurityPolicy",
                    "metadata": {
                        "name": "aaa-$(workshop_namespace)-docker",
                        "labels": {
                            f"training.{OPERATOR_API_GROUP}/component": "environment",
                            f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                            f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                            f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        },
                    },
                    "spec": {
                        "allowPrivilegeEscalation": True,
                        "fsGroup": {
                            "ranges": [{"max": 65535, "min": 0}],
                            "rule": "MustRunAs",
                        },
                        "hostIPC": False,
                        "hostNetwork": False,
                        "hostPID": False,
                        "hostPorts": [],
                        "privileged": True,
                        "requiredDropCapabilities": [
                            "KILL",
                            "MKNOD",
                            "SETUID",
                            "SETGID",
                        ],
                        "runAsUser": {"rule": "RunAsAny"},
                        "seLinux": {"rule": "RunAsAny"},
                        "supplementalGroups": {
                            "ranges": [{"max": 65535, "min": 0}],
                            "rule": "MustRunAs",
                        },
                        "volumes": [
                            "configMap",
                            "downwardAPI",
                            "emptyDir",
                            "persistentVolumeClaim",
                            "projected",
                            "secret",
                        ],
                    },
                },
                {
                    "apiVersion": "rbac.authorization.k8s.io/v1",
                    "kind": "ClusterRole",
                    "metadata": {
                        "name": "$(workshop_namespace)-docker",
                        "labels": {
                            f"training.{OPERATOR_API_GROUP}/component": "environment",
                            f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                            f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                            f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        },
                    },
                    "rules": [
                        {
                            "apiGroups": ["policy"],
                            "resources": ["podsecuritypolicies"],
                            "verbs": ["use"],
                            "resourceNames": ["aaa-$(workshop_namespace)-docker"],
                        }
                    ],
                },
            ]
        )

    policy_objects.extend(
        [
            {
                "apiVersion": "policy/v1beta1",
                "kind": "PodSecurityPolicy",
                "metadata": {
                    "name": "aaa-$(workshop_namespace)-nonroot",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    },
                },
                "spec": {
                    "allowPrivilegeEscalation": False,
                    "fsGroup": {
                        "ranges": [{"max": 65535, "min": 0}],
                        "rule": "MustRunAs",
                    },
                    "hostIPC": False,
                    "hostNetwork": False,
                    "hostPID": False,
                    "hostPorts": [],
                    "privileged": False,
                    "requiredDropCapabilities": ["ALL"],
                    "runAsUser": {"rule": "MustRunAsNonRoot"},
                    "seLinux": {"rule": "RunAsAny"},
                    "supplementalGroups": {
                        "ranges": [{"max": 65535, "min": 0}],
                        "rule": "MustRunAs",
                    },
                    "volumes": [
                        "configMap",
                        "downwardAPI",
                        "emptyDir",
                        "persistentVolumeClaim",
                        "projected",
                        "secret",
                    ],
                },
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRole",
                "metadata": {
                    "name": "$(workshop_namespace)-nonroot",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    },
                },
                "rules": [
                    {
                        "apiGroups": ["policy"],
                        "resources": ["podsecuritypolicies"],
                        "verbs": ["use"],
                        "resourceNames": ["aaa-$(workshop_namespace)-nonroot"],
                    }
                ],
            },
            {
                "apiVersion": "policy/v1beta1",
                "kind": "PodSecurityPolicy",
                "metadata": {
                    "name": "aaa-$(workshop_namespace)-anyuid",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    },
                },
                "spec": {
                    "allowPrivilegeEscalation": False,
                    "fsGroup": {
                        "ranges": [{"max": 65535, "min": 0}],
                        "rule": "MustRunAs",
                    },
                    "hostIPC": False,
                    "hostNetwork": False,
                    "hostPID": False,
                    "hostPorts": [],
                    "privileged": False,
                    "requiredDropCapabilities": ["ALL"],
                    "defaultAddCapabilities": ["NET_BIND_SERVICE"],
                    "runAsUser": {"rule": "RunAsAny"},
                    "seLinux": {"rule": "RunAsAny"},
                    "supplementalGroups": {
                        "ranges": [{"max": 65535, "min": 0}],
                        "rule": "MustRunAs",
                    },
                    "volumes": [
                        "configMap",
                        "downwardAPI",
                        "emptyDir",
                        "persistentVolumeClaim",
                        "projected",
                        "secret",
                    ],
                },
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRole",
                "metadata": {
                    "name": "$(workshop_namespace)-anyuid",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    },
                },
                "rules": [
                    {
                        "apiGroups": ["policy"],
                        "resources": ["podsecuritypolicies"],
                        "verbs": ["use"],
                        "resourceNames": ["aaa-$(workshop_namespace)-anyuid"],
                    }
                ],
            },
        ]
    )

    for object_body in policy_objects:
        object_body = _substitute_variables(object_body)
        kopf.adopt(object_body)
        create_from_dict(object_body)

    # Create a service account for running any services in the workshop
    # namespace such as session specific or mirror container registries.

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": f"{RESOURCE_NAME_PREFIX}-services",
            "namespace": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "environment",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
            },
        },
    }

    pykube.ServiceAccount(api, service_account_body).create()

    # Create role binding in the workshop namespace granting the service
    # account for running any services default role access.

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": f"{RESOURCE_NAME_PREFIX}-services",
            "namespace": workshop_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "environment",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{workshop_namespace}-nonroot",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": f"{RESOURCE_NAME_PREFIX}-services",
                "namespace": workshop_namespace,
            }
        ],
    }

    pykube.RoleBinding(api, role_binding_body).create()

    # If docker is enabled and system profile indicates that a registry
    # mirror should be used, we deploy a registry mirror in the workshop
    # namespace. We only need to expose it via a service, not an ingress
    # as the dockerd is in the same namespace and can talk to it direct.

    if applications.is_enabled("docker"):
        mirror_remote = operator_dockerd_mirror_remote(system_profile)
        mirror_username = operator_dockerd_mirror_username(system_profile)
        mirror_password = operator_dockerd_mirror_password(system_profile)

        if mirror_remote:
            mirror_objects = []

            default_storage_class = operator_storage_class(system_profile)
            default_storage_user = operator_storage_user(system_profile)
            default_storage_group = operator_storage_group(system_profile)

            mirror_memory = applications.property("registry", "memory", "768Mi")
            mirror_storage = applications.property("docker", "storage", "5Gi")

            mirror_persistent_volume_claim_body = {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{workshop_namespace}-mirror",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    },
                },
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": mirror_storage}},
                },
            }

            if default_storage_class:
                mirror_persistent_volume_claim_body["spec"][
                    "storageClassName"
                ] = default_storage_class

            mirror_deployment_body = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{workshop_namespace}-mirror",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                        f"training.{OPERATOR_API_GROUP}/environment.services.mirror": "true",
                    },
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": {"deployment": f"{workshop_namespace}-mirror"}
                    },
                    "strategy": {"type": "Recreate"},
                    "template": {
                        "metadata": {
                            "labels": {
                                "deployment": f"{workshop_namespace}-mirror",
                                f"training.{OPERATOR_API_GROUP}/component": "environment",
                                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                                f"training.{OPERATOR_API_GROUP}/environment.services.mirror": "true",
                            },
                        },
                        "spec": {
                            "serviceAccountName": f"{RESOURCE_NAME_PREFIX}-services",
                            "initContainers": [],
                            "containers": [
                                {
                                    "name": "registry",
                                    "image": "registry.hub.docker.com/library/registry:2.6.1",
                                    "imagePullPolicy": "IfNotPresent",
                                    "resources": {
                                        "limits": {"memory": mirror_memory},
                                        "requests": {"memory": mirror_memory},
                                    },
                                    "ports": [
                                        {"containerPort": 5000, "protocol": "TCP"}
                                    ],
                                    "env": [
                                        {
                                            "name": "REGISTRY_STORAGE_DELETE_ENABLED",
                                            "value": "true",
                                        },
                                        {
                                            "name": "REGISTRY_PROXY_REMOTEURL",
                                            "value": mirror_remote,
                                        },
                                        {
                                            "name": "REGISTRY_PROXY_USERNAME",
                                            "value": mirror_username,
                                        },
                                        {
                                            "name": "REGISTRY_PROXY_PASSWORD",
                                            "value": mirror_password,
                                        },
                                    ],
                                    "volumeMounts": [
                                        {
                                            "name": "data",
                                            "mountPath": "/var/lib/registry",
                                        },
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
                                        "claimName": f"{workshop_namespace}-mirror"
                                    },
                                },
                            ],
                        },
                    },
                },
            }

            mirror_service_body = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "namespace": workshop_namespace,
                    "name": f"{workshop_namespace}-mirror",
                    "labels": {
                        f"training.{OPERATOR_API_GROUP}/component": "environment",
                        f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                    },
                },
                "spec": {
                    "type": "ClusterIP",
                    "ports": [{"port": 5000, "targetPort": 5000}],
                    "selector": {"deployment": f"{workshop_namespace}-mirror"},
                },
            }

            mirror_objects.extend(
                [
                    mirror_persistent_volume_claim_body,
                    mirror_deployment_body,
                    mirror_service_body,
                ]
            )

            for object_body in mirror_objects:
                object_body = _substitute_variables(object_body)
                kopf.adopt(object_body)
                create_from_dict(object_body)

    # Save away the specification of the workshop in the status for the
    # custom resourcse. We will use this later when creating any
    # workshop instances so always working with the same version.

    return {
        "phase": "Running",
        "namespace": workshop_namespace,
        "secrets": {"ingress": ingress_secrets, "registry": image_pull_secrets},
        "workshop": {
            "name": workshop_name,
            "uid": workshop_uid,
            "generation": workshop_generation,
            "spec": workshop_spec,
        },
    }


@kopf.on.delete(
    f"training.{OPERATOR_API_GROUP}", "v1alpha1", "workshopenvironments", optional=True
)
def workshop_environment_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
