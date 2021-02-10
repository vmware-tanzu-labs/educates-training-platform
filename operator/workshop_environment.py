import os
import yaml

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

from system_profile import (
    operator_ingress_domain,
    operator_ingress_protocol,
    operator_ingress_secret,
    operator_storage_class,
    operator_storage_user,
    operator_storage_group,
    operator_dockerd_mirror_remote,
    operator_dockerd_mirror_username,
    operator_dockerd_mirror_password,
    environment_image_pull_secrets,
    registry_image_pull_secret,
    theme_dashboard_script,
    theme_dashboard_style,
    theme_workshop_script,
    theme_workshop_style,
)

from objects import create_from_dict
from helpers import Applications

__all__ = ["workshop_environment_create", "workshop_environment_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshopenvironments", id="eduk8s")
def workshop_environment_create(name, meta, spec, logger, **_):
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Use the name of the custom resource as the name of the namespace
    # under which the workshop environment is created and any workshop
    # instances are created.

    environment_name = name
    workshop_namespace = environment_name

    # Can optionally be passed name of the training portal via a label
    # when the workshop environment is created as a child to a training
    # portal.

    portal_name = meta.get("labels", {}).get("training.eduk8s.io/portal.name", "")

    # The name of the workshop to be deployed can differ and is taken
    # from the specification of the workspace. Lookup the workshop
    # resource definition and ensure it exists. Later we will stash a
    # copy of this in the status of the custom resource, and we will use
    # this copy to avoid being affected by changes in the original after
    # the creation of the workshop environment.

    workshop_name = spec["workshop"]["name"]

    try:
        workshop_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha2", "workshops", workshop_name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise kopf.TemporaryError(f"Workshop {workshop_name} is not available.")

    try:
        del workshop_instance["metadata"]["annotations"][
            "kubectl.kubernetes.io/last-applied-configuration"
        ]
    except KeyError:
        pass

    workshop_uid = workshop_instance["metadata"]["uid"]
    workshop_generation = workshop_instance["metadata"]["generation"]
    workshop_spec = workshop_instance.get("spec", {})

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
                "training.eduk8s.io/component": "environment",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
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
        namespace_instance = core_api.create_namespace(body=namespace_body)
    except kubernetes.client.rest.ApiException as e:
        if e.status == 409:
            raise kopf.TemporaryError(f"Namespace {workshop_namespace} already exists.")
        raise

    # Delete any limit ranges applied to the namespace so they don't
    # cause issues with workshop instance deployments or any workshop
    # deployments.

    limit_ranges = core_api.list_namespaced_limit_range(namespace=workshop_namespace)

    for limit_range in limit_ranges.items:
        core_api.delete_namespaced_limit_range(
            namespace=workshop_namespace, name=limit_range.metadata.name
        )

    # Delete any resource quotas applied to the namespace so they don't
    # cause issues with workshop instance deploymemnts or any workshop
    # resources.

    resource_quotas = core_api.list_namespaced_resource_quota(
        namespace=workshop_namespace
    )

    for resource_quota in resource_quotas.items:
        core_api.delete_namespaced_resource_quota(
            namespace=workshop_namespace, name=resource_quota.metadata.name
        )

    # Create a config map in the workshop namespace which contains the
    # details about the workshop. This will be mounted into workshop
    # instances so they can derive information to configure themselves.

    system_profile = spec.get("system", {}).get("profile")

    dashboard_js = theme_dashboard_script(system_profile)
    dashboard_css = theme_dashboard_style(system_profile)
    workshop_js = theme_workshop_script(system_profile)
    workshop_css = theme_workshop_style(system_profile)

    workshop_data = yaml.dump(workshop_instance, Dumper=yaml.Dumper)

    config_map_body = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "workshop",
            "labels": {
                "training.eduk8s.io/component": "environment",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
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

    core_api.create_namespaced_config_map(
        namespace=workshop_namespace, body=config_map_body
    )

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
                "training.eduk8s.io/component": "environment",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
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

    cluster_role_instance = rbac_authorization_api.create_cluster_role(
        body=cluster_role_body
    )

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

    ingress_secrets = []

    if ingress_secret:
        try:
            ingress_secret_instance = core_api.read_namespaced_secret(
                namespace="eduk8s", name=ingress_secret
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(
                    f"TLS secret {ingress_secret} is not available."
                )
            raise

        if (
            ingress_secret_instance.type != "kubernetes.io/tls"
            or not ingress_secret_instance.data.get("tls.crt")
            or not ingress_secret_instance.data.get("tls.key")
        ):
            raise kopf.TemporaryError(f"TLS secret {ingress_secret} is not valid.")

        ingress_protocol = "https"

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": ingress_secret,
                "labels": {
                    "training.eduk8s.io/component": "environment",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                },
            },
            "type": "kubernetes.io/tls",
            "data": ingress_secret_instance.data,
        }

        core_api.create_namespaced_secret(
            namespace=workshop_namespace, body=secret_body
        )

        ingress_secrets.append(ingress_secret)

    # Make copies of any pull secrets into the workshop namespace.

    image_pull_secrets = list(environment_image_pull_secrets(system_profile))

    pull_secret_name = registry_image_pull_secret(system_profile)

    if pull_secret_name and pull_secret_name not in image_pull_secrets:
        image_pull_secrets.append(pull_secret_name)

    for pull_secret_name in image_pull_secrets:
        try:
            pull_secret_instance = core_api.read_namespaced_secret(
                namespace="eduk8s", name=pull_secret_name
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(
                    f"Pull secret {pull_secret_name} is not available."
                )
            raise

        if (
            pull_secret_instance.type != "kubernetes.io/dockerconfigjson"
            or not pull_secret_instance.data.get(".dockerconfigjson")
        ):
            raise kopf.TemporaryError(f"Pull secret {pull_secret_name} is not valid.")

        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": pull_secret_name,
                "labels": {
                    "training.eduk8s.io/component": "environment",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                },
            },
            "type": "kubernetes.io/dockerconfigjson",
            "data": pull_secret_instance.data,
        }

        core_api.create_namespaced_secret(
            namespace=workshop_namespace, body=secret_body
        )

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
            obj = obj.replace("$(ingress_domain)", ingress_domain)
            obj = obj.replace("$(ingress_protocol)", ingress_protocol)
            obj = obj.replace("$(ingress_port_suffix)", "")
            obj = obj.replace("$(ingress_secret)", ingress_secret)
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
                    "training.eduk8s.io/component": "environment",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/environment.objects": "true",
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
                    "training.eduk8s.io/component": "environment",
                    "training.eduk8s.io/workshop.name": workshop_name,
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
                    "training.eduk8s.io/environment.objects": "true",
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
                            "training.eduk8s.io/component": "environment",
                            "training.eduk8s.io/workshop.name": workshop_name,
                            "training.eduk8s.io/portal.name": portal_name,
                            "training.eduk8s.io/environment.name": environment_name,
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
                            "training.eduk8s.io/component": "environment",
                            "training.eduk8s.io/workshop.name": workshop_name,
                            "training.eduk8s.io/portal.name": portal_name,
                            "training.eduk8s.io/environment.name": environment_name,
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
                    "name": "aaa-$(workshop_namespace)-default",
                    "labels": {
                        "training.eduk8s.io/component": "environment",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
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
                    "name": "$(workshop_namespace)-default",
                    "labels": {
                        "training.eduk8s.io/component": "environment",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
                    },
                },
                "rules": [
                    {
                        "apiGroups": ["policy"],
                        "resources": ["podsecuritypolicies"],
                        "verbs": ["use"],
                        "resourceNames": ["aaa-$(workshop_namespace)-default"],
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
            "name": "eduk8s-services",
            "labels": {
                "training.eduk8s.io/component": "environment",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
            },
        },
    }

    core_api.create_namespaced_service_account(
        namespace=workshop_namespace, body=service_account_body
    )

    # Create role binding in the workshop namespace granting the service
    # account for running any services default role access.

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": "eduk8s-services",
            "labels": {
                "training.eduk8s.io/component": "environment",
                "training.eduk8s.io/workshop.name": workshop_name,
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/environment.name": environment_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"aaa-{workshop_namespace}-default",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "eduk8s-services",
                "namespace": workshop_namespace,
            }
        ],
    }

    rbac_authorization_api.create_namespaced_role_binding(
        namespace=workshop_namespace, body=role_binding_body
    )

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
                        "training.eduk8s.io/component": "environment",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
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
                        "training.eduk8s.io/component": "environment",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
                        "training.eduk8s.io/environment.services.mirror": "true",
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
                                "training.eduk8s.io/component": "environment",
                                "training.eduk8s.io/workshop.name": workshop_name,
                                "training.eduk8s.io/portal.name": portal_name,
                                "training.eduk8s.io/environment.name": environment_name,
                                "training.eduk8s.io/environment.services.mirror": "true",
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
                        "training.eduk8s.io/component": "environment",
                        "training.eduk8s.io/workshop.name": workshop_name,
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/environment.name": environment_name,
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
        "namespace": workshop_namespace,
        "secrets": {"ingress": ingress_secrets, "registry": image_pull_secrets},
        "workshop": {
            "name": workshop_name,
            "uid": workshop_uid,
            "generation": workshop_generation,
            "spec": workshop_spec,
        },
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshopenvironments", optional=True)
def workshop_environment_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
