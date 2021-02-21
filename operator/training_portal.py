import os
import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

from system_profile import (
    portal_admin_username,
    portal_admin_password,
    portal_robot_username,
    portal_robot_password,
    portal_robot_client_id,
    portal_robot_client_secret,
    operator_ingress_domain,
    operator_ingress_protocol,
    operator_ingress_secret,
    operator_ingress_class,
    operator_storage_class,
    operator_storage_user,
    operator_storage_group,
    portal_container_image,
    registry_image_pull_secret,
    theme_portal_script,
    theme_portal_style,
    analytics_google_tracking_id,
)

__all__ = ["training_portal_create", "training_portal_delete"]


@kopf.on.create(
    "training.eduk8s.io", "v1alpha1", "trainingportals", id="eduk8s", timeout=900
)
def training_portal_create(name, uid, spec, logger, **_):
    apps_api = kubernetes.client.AppsV1Api()
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    extensions_api = kubernetes.client.ExtensionsV1beta1Api()
    policy_api = kubernetes.client.PolicyV1beta1Api()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Set name for the portal namespace. The ingress used to access the portal
    # can be overridden, but namespace is always the same.

    portal_name = name
    portal_namespace = f"{portal_name}-ui"

    # Determine URL to be used for accessing the portal web interface.

    system_profile = spec.get("system", {}).get("profile")

    default_ingress_domain = operator_ingress_domain(system_profile)
    default_ingress_protocol = operator_ingress_protocol(system_profile)
    default_ingress_secret = operator_ingress_secret(system_profile)
    default_ingress_class = operator_ingress_class(system_profile)

    ingress_hostname = spec.get("portal", {}).get("ingress", {}).get("hostname")

    ingress_protocol = default_ingress_protocol

    ingress_domain = (
        spec.get("portal", {}).get("ingress", {}).get("domain", default_ingress_domain)
    )

    ingress_class = (
        spec.get("portal", {}).get("ingress", {}).get("class", default_ingress_class)
    )

    if not ingress_hostname:
        portal_hostname = f"{portal_name}-ui.{ingress_domain}"
    elif not "." in ingress_hostname:
        portal_hostname = f"{ingress_hostname}.{ingress_domain}"
    else:
        portal_hostname = ingress_hostname

    if ingress_domain == default_ingress_domain:
        ingress_secret = default_ingress_secret
    else:
        ingress_secret = spec.get("portal", {}).get("ingress", {}).get("secret", "")

    # If a TLS secret is specified, ensure that the secret exists in the
    # eduk8s namespace.

    ingress_secret_instance = None

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

    # If a registry image pull secret is specified, ensure that the secret
    # exists in the eduk8s namespace.

    pull_secret_instance = None

    pull_secret = registry_image_pull_secret(system_profile)

    if pull_secret:
        try:
            pull_secret_instance = core_api.read_namespaced_secret(
                namespace="eduk8s", name=pull_secret
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(
                    f"Image pull secret {pull_secret} is not available."
                )
            raise

        if (
            pull_secret_instance.type != "kubernetes.io/dockerconfigjson"
            or not pull_secret_instance.data.get(".dockerconfigjson")
        ):
            raise kopf.TemporaryError(
                f"Image pull secret {ingress_secret} is not valid."
            )

    # Generate an admin password and api credentials for portal management.

    characters = string.ascii_letters + string.digits

    credentials = spec.get("portal", {}).get("credentials", {})

    admin_credentials = credentials.get("admin", {})
    robot_credentials = credentials.get("robot", {})

    clients = spec.get("portal", {}).get("clients", {})

    robot_client = clients.get("robot", {})

    default_admin_username = portal_admin_username(system_profile)
    default_admin_password = portal_admin_password(system_profile)
    default_robot_username = portal_robot_username(system_profile)
    default_robot_password = portal_robot_password(system_profile)
    default_robot_client_id = portal_robot_client_id(system_profile)
    default_robot_client_secret = portal_robot_client_secret(system_profile)

    admin_username = admin_credentials.get("username", default_admin_username)
    admin_password = admin_credentials.get("password", default_admin_password)
    robot_username = robot_credentials.get("username", default_robot_username)
    robot_password = robot_credentials.get("password", default_robot_password)
    robot_client_id = robot_client.get("id", default_robot_client_id)
    robot_client_secret = robot_client.get("secret", default_robot_client_secret)

    # Create the namespace for holding the web interface for the portal.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": portal_namespace,
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
    }

    # Make the namespace for the portal a child of the custom resource for the
    # training portal. This way the namespace will be automatically deleted
    # when the resource definition for the training portal is deleted and we
    # don't have to clean up anything explicitly.

    kopf.adopt(namespace_body)

    try:
        namespace_instance = core_api.create_namespace(body=namespace_body)
    except kubernetes.client.rest.ApiException as e:
        if e.status == 409:
            raise kopf.TemporaryError(f"Namespace {portal_namespace} already exists.")
        raise

    # Delete any limit ranges applied to the namespace so they don't cause
    # issues with deploying the training portal.

    limit_ranges = core_api.list_namespaced_limit_range(namespace=portal_namespace)

    for limit_range in limit_ranges.items:
        core_api.delete_namespaced_limit_range(
            namespace=portal_namespace, name=limit_range.metadata.name
        )

    # Delete any resource quotas applied to the namespace so they don't cause
    # issues with deploying the training portal.

    resource_quotas = core_api.list_namespaced_resource_quota(
        namespace=portal_namespace
    )

    for resource_quota in resource_quotas.items:
        core_api.delete_namespaced_resource_quota(
            namespace=portal_namespace, name=resource_quota.metadata.name
        )

    # Make a copy of the TLS secret into the portal namespace.

    ingress_secrets = []

    if ingress_secret:
        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": ingress_secret,
                "labels": {
                    "training.eduk8s.io/component": "portal",
                    "training.eduk8s.io/portal.name": portal_name,
                },
            },
            "type": "kubernetes.io/tls",
            "data": ingress_secret_instance.data,
        }

        core_api.create_namespaced_secret(namespace=portal_namespace, body=secret_body)

        ingress_secrets.append(ingress_secret)

    # Deploy the training portal web interface. First up need to create a
    # service account and bind required roles to it.

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": "eduk8s-portal",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
    }

    pull_secrets = []

    if pull_secret:
        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": pull_secret,
                "labels": {
                    "training.eduk8s.io/component": "portal",
                    "training.eduk8s.io/portal.name": portal_name,
                },
            },
            "type": "kubernetes.io/dockerconfigjson",
            "data": pull_secret_instance.data,
        }

        core_api.create_namespaced_secret(namespace=portal_namespace, body=secret_body)

        service_account_body["imagePullSecrets"] = [{"name": pull_secret}]

        pull_secrets.append(pull_secret)

    core_api.create_namespaced_service_account(
        namespace=portal_namespace, body=service_account_body
    )

    pod_security_policy_body = {
        "apiVersion": "policy/v1beta1",
        "kind": "PodSecurityPolicy",
        "metadata": {
            "name": f"aaa-{portal_namespace}",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
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
    }

    kopf.adopt(pod_security_policy_body)

    policy_api.create_pod_security_policy(body=pod_security_policy_body)

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": f"{portal_namespace}-policy",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "rules": [
            {
                "apiGroups": ["policy"],
                "resources": [
                    "podsecuritypolicies",
                ],
                "verbs": ["use"],
                "resourceNames": [f"aaa-{portal_namespace}"],
            },
        ],
    }

    kopf.adopt(cluster_role_body)

    rbac_authorization_api.create_cluster_role(body=cluster_role_body)

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": f"{portal_namespace}-eduk8s",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "rules": [
            {
                "apiGroups": ["training.eduk8s.io"],
                "resources": [
                    "workshops",
                    "workshopenvironments",
                    "workshopsessions",
                    "trainingportals",
                ],
                "verbs": ["get", "list", "watch"],
            },
            {
                "apiGroups": ["training.eduk8s.io"],
                "resources": [
                    "workshopenvironments",
                    "workshopsessions",
                ],
                "verbs": ["create", "patch", "delete"],
            },
        ],
    }

    kopf.adopt(cluster_role_body)

    rbac_authorization_api.create_cluster_role(body=cluster_role_body)

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": f"{portal_namespace}-eduk8s",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{portal_namespace}-eduk8s",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "eduk8s-portal",
                "namespace": portal_namespace,
            }
        ],
    }

    kopf.adopt(cluster_role_binding_body)

    rbac_authorization_api.create_cluster_role_binding(body=cluster_role_binding_body)

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": f"eduk8s-portal-policy",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{portal_namespace}-policy",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "eduk8s-portal",
                "namespace": portal_namespace,
            }
        ],
    }

    kopf.adopt(role_binding_body)

    rbac_authorization_api.create_namespaced_role_binding(
        namespace=portal_namespace, body=role_binding_body
    )

    # Allocate a persistent volume for storage of the database.

    default_storage_class = operator_storage_class(system_profile)
    default_storage_user = operator_storage_user(system_profile)
    default_storage_group = operator_storage_group(system_profile)

    persistent_volume_claim_body = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": "eduk8s-portal",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": "1Gi"}},
        },
    }

    if default_storage_class:
        persistent_volume_claim_body["spec"]["storageClassName"] = default_storage_class

    core_api.create_namespaced_persistent_volume_claim(
        namespace=portal_namespace, body=persistent_volume_claim_body
    )

    # Next create the deployment for the portal web interface.

    default_google_tracking_id = analytics_google_tracking_id(system_profile)

    portal_image = spec.get("portal", {}).get("image", portal_container_image())

    portal_title = spec.get("portal", {}).get("title", "Workshops")

    portal_password = spec.get("portal", {}).get("password", "")

    portal_index = spec.get("portal", {}).get("index", "")

    portal_logo = spec.get("portal", {}).get("logo", "")

    frame_ancestors = (
        spec.get("portal", {}).get("theme", {}).get("frame", {}).get("ancestors", [])
    )
    frame_ancestors = ",".join(frame_ancestors)

    registration_type = (
        spec.get("portal", {}).get("registration", {}).get("type", "one-step")
    )

    enable_registration = str(
        spec.get("portal", {}).get("registration", {}).get("enabled", True)
    ).lower()

    catalog_visibility = (
        spec.get("portal", {}).get("catalog", {}).get("visibility", "private")
    )

    portal_google_tracking_id = (
        spec.get("analytics", {})
        .get("google", {})
        .get("trackingId", default_google_tracking_id)
    )

    image_pull_policy = "IfNotPresent"

    if (
        portal_image.endswith(":master")
        or portal_image.endswith(":develop")
        or portal_image.endswith(":latest")
        or ":" not in portal_image
    ):
        image_pull_policy = "Always"

    portal_js = theme_portal_script(system_profile)
    portal_css = theme_portal_style(system_profile)

    config_map_body = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": f"eduk8s-portal",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "data": {
            "logo": portal_logo,
            "theme.js": portal_js,
            "theme.css": portal_css,
        },
    }

    core_api.create_namespaced_config_map(
        namespace=portal_namespace, body=config_map_body
    )

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "eduk8s-portal",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
                "training.eduk8s.io/portal.services.dashboard": "true",
            },
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": "eduk8s-portal"}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {
                    "labels": {
                        "deployment": "eduk8s-portal",
                        "training.eduk8s.io/component": "portal",
                        "training.eduk8s.io/portal.name": portal_name,
                        "training.eduk8s.io/portal.services.dashboard": "true",
                    },
                },
                "spec": {
                    "serviceAccountName": "eduk8s-portal",
                    "securityContext": {
                        "fsGroup": default_storage_group,
                        "supplementalGroups": [default_storage_group],
                    },
                    "containers": [
                        {
                            "name": "portal",
                            "image": portal_image,
                            "imagePullPolicy": image_pull_policy,
                            "resources": {
                                "requests": {"memory": "256Mi"},
                                "limits": {"memory": "256Mi"},
                            },
                            "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                            "readinessProbe": {
                                "httpGet": {"path": "/accounts/login/", "port": 8080},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 10,
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/accounts/login/", "port": 8080},
                                "initialDelaySeconds": 15,
                                "periodSeconds": 10,
                            },
                            "env": [
                                {
                                    "name": "TRAINING_PORTAL",
                                    "value": portal_name,
                                },
                                {
                                    "name": "PORTAL_UID",
                                    "value": uid,
                                },
                                {
                                    "name": "PORTAL_HOSTNAME",
                                    "value": portal_hostname,
                                },
                                {
                                    "name": "PORTAL_TITLE",
                                    "value": portal_title,
                                },
                                {
                                    "name": "PORTAL_PASSWORD",
                                    "value": portal_password,
                                },
                                {
                                    "name": "PORTAL_INDEX",
                                    "value": portal_index,
                                },
                                {
                                    "name": "FRAME_ANCESTORS",
                                    "value": frame_ancestors,
                                },
                                {
                                    "name": "ADMIN_USERNAME",
                                    "value": admin_username,
                                },
                                {
                                    "name": "ADMIN_PASSWORD",
                                    "value": admin_password,
                                },
                                {
                                    "name": "INGRESS_DOMAIN",
                                    "value": ingress_domain,
                                },
                                {
                                    "name": "REGISTRATION_TYPE",
                                    "value": registration_type,
                                },
                                {
                                    "name": "ENABLE_REGISTRATION",
                                    "value": enable_registration,
                                },
                                {
                                    "name": "CATALOG_VISIBILITY",
                                    "value": catalog_visibility,
                                },
                                {
                                    "name": "INGRESS_CLASS",
                                    "value": ingress_class,
                                },
                                {
                                    "name": "INGRESS_PROTOCOL",
                                    "value": ingress_protocol,
                                },
                                {
                                    "name": "INGRESS_SECRET",
                                    "value": ingress_secret,
                                },
                                {
                                    "name": "GOOGLE_TRACKING_ID",
                                    "value": portal_google_tracking_id,
                                },
                            ],
                            "volumeMounts": [
                                {"name": "data", "mountPath": "/opt/app-root/data"},
                                {"name": "config", "mountPath": "/opt/app-root/config"},
                            ],
                        }
                    ],
                    "volumes": [
                        {
                            "name": "data",
                            "persistentVolumeClaim": {"claimName": "eduk8s-portal"},
                        },
                        {
                            "name": "config",
                            "configMap": {"name": "eduk8s-portal"},
                        },
                    ],
                },
            },
        },
    }

    # This hack is to cope with Kubernetes clusters which don't properly
    # set up persistent volume ownership. IBM Kubernetes is one example.
    # The init container runs as root and sets permissions on the storage
    # and ensures it is group writable. Note that this will only work
    # where pod security policies are not enforced. Don't attempt to use
    # it if they are. If they are, this hack should not be required.

    if default_storage_user:
        storage_init_container = {
            "name": "storage-permissions-initialization",
            "image": portal_image,
            "imagePullPolicy": image_pull_policy,
            "securityContext": {"runAsUser": 0},
            "command": ["/bin/sh", "-c"],
            "args": [
                f"chown {default_storage_user}:{default_storage_group} /mnt && chmod og+rwx /mnt"
            ],
            "resources": {
                "requests": {"memory": "256Mi"},
                "limits": {"memory": "256Mi"},
            },
            "volumeMounts": [{"name": "data", "mountPath": "/mnt"}],
        }

        deployment_body["spec"]["template"]["spec"]["initContainers"] = [
            storage_init_container
        ]

    apps_api.create_namespaced_deployment(
        namespace=portal_namespace, body=deployment_body
    )

    # Finally expose the deployment via a service and ingress route.

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "eduk8s-portal",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
        },
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 8080, "protocol": "TCP", "targetPort": 8080}],
            "selector": {"deployment": "eduk8s-portal"},
        },
    }

    core_api.create_namespaced_service(namespace=portal_namespace, body=service_body)

    ingress_body = {
        "apiVersion": "extensions/v1beta1",
        "kind": "Ingress",
        "metadata": {
            "name": "eduk8s-portal",
            "labels": {
                "training.eduk8s.io/component": "portal",
                "training.eduk8s.io/portal.name": portal_name,
            },
            "annotations": {},
        },
        "spec": {
            "rules": [
                {
                    "host": portal_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "backend": {
                                    "serviceName": "eduk8s-portal",
                                    "servicePort": 8080,
                                },
                            }
                        ]
                    },
                }
            ]
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
                "hosts": [portal_hostname],
                "secretName": ingress_secret,
            }
        ]

    portal_url = f"{ingress_protocol}://{portal_hostname}"

    extensions_api.create_namespaced_ingress(
        namespace=portal_namespace, body=ingress_body
    )

    # Save away the details of the portal which was created in status.

    return {
        "namespace": portal_namespace,
        "url": portal_url,
        "credentials": {
            "admin": {"username": admin_username, "password": admin_password},
            "robot": {"username": robot_username, "password": robot_password},
        },
        "clients": {"robot": {"id": robot_client_id, "secret": robot_client_secret}},
        "secrets": {"ingress": ingress_secrets, "registry": pull_secrets},
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "trainingportals", optional=True)
def training_portal_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
