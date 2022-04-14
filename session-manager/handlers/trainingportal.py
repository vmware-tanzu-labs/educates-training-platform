import pykube
import kopf

from .system_profile import (
    portal_admin_username,
    portal_admin_password,
    portal_robot_username,
    portal_robot_password,
    portal_robot_client_id,
    portal_robot_client_secret,
    training_portal_image,
)

from .config import (
    OPERATOR_API_GROUP,
    RESOURCE_STATUS_KEY,
    RESOURCE_NAME_PREFIX,
    INGRESS_DOMAIN,
    INGRESS_PROTOCOL,
    INGRESS_SECRET,
    INGRESS_CLASS,
    STORAGE_CLASS,
    STORAGE_USER,
    STORAGE_GROUP,
    GOOGLE_TRACKING_ID,
    THEME_PORTAL_SCRIPT,
    THEME_PORTAL_STYLE,
)

__all__ = ["training_portal_create", "training_portal_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "trainingportals",
    id=RESOURCE_STATUS_KEY,
    timeout=900,
)
def training_portal_create(name, uid, spec, patch, logger, **_):
    # Set name for the portal namespace. The hostname used to access the portal
    # can be overridden, but namespace is always the same.

    portal_name = name
    portal_namespace = f"{portal_name}-ui"

    ingress_hostname = spec.get("portal", {}).get("ingress", {}).get("hostname")

    if not ingress_hostname:
        portal_hostname = f"{portal_name}-ui.{INGRESS_DOMAIN}"
    elif not "." in ingress_hostname:
        portal_hostname = f"{ingress_hostname}.{INGRESS_DOMAIN}"
    else:
        portal_hostname = ingress_hostname

    # Generate an admin password and api credentials for portal management.

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
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
            "annotations": {"secretgen.carvel.dev/excluded-from-wildcard-matching": ""},
        },
    }

    # Make the namespace for the portal a child of the custom resource for the
    # training portal. This way the namespace will be automatically deleted
    # when the resource definition for the training portal is deleted and we
    # don't have to clean up anything explicitly.

    kopf.adopt(namespace_body)

    try:
        namespace_instance = pykube.Namespace(api, namespace_body).create()

    except pykube.exceptions.KubernetesError as e:
        if e.code == 409:
            patch["status"] = {RESOURCE_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(f"Namespace {portal_namespace} already exists.")
        raise

    # Delete any limit ranges applied to the namespace so they don't cause
    # issues with deploying the training portal. This can be an issue where
    # namespace/project templates apply them automatically to a namespace. The
    # problem is that we may do this query too quickly and they may not have
    # been created as yet.

    for limit_range in pykube.LimitRange.objects(api, namespace=portal_namespace).all():
        try:
            limit_range.delete()
        except pykube.exceptions.ObjectDoesNotExist:
            pass

    # Delete any resource quotas applied to the namespace so they don't cause
    # issues with deploying the training portal. This can be an issue where
    # namespace/project templates apply them automatically to a namespace. The
    # problem is that we may do this query too quickly and they may not have
    # been created as yet.

    for resource_quota in pykube.ResourceQuota.objects(
        api, namespace=portal_namespace
    ).all():
        try:
            resource_quota.delete()
        except pykube.exceptions.ObjectDoesNotExist:
            pass

    # Deploy the training portal web interface. First up need to create a
    # service account and bind required roles to it.

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": "training-portal",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
    }

    pykube.ServiceAccount(api, service_account_body).create()

    pod_security_policy_body = {
        "apiVersion": "policy/v1beta1",
        "kind": "PodSecurityPolicy",
        "metadata": {
            "name": f"aaa-{RESOURCE_NAME_PREFIX}-nonroot-security-policy-{portal_namespace}",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
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

    pykube.PodSecurityPolicy(api, pod_security_policy_body).create()

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": f"{RESOURCE_NAME_PREFIX}-nonroot-security-policy-{portal_namespace}",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "rules": [
            {
                "apiGroups": ["policy"],
                "resources": [
                    "podsecuritypolicies",
                ],
                "verbs": ["use"],
                "resourceNames": [
                    f"aaa-{RESOURCE_NAME_PREFIX}-nonroot-security-policy-{portal_namespace}"
                ],
            },
        ],
    }

    kopf.adopt(cluster_role_body)

    pykube.ClusterRole(api, cluster_role_body).create()

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": f"{RESOURCE_NAME_PREFIX}-training-portal-{portal_namespace}",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "rules": [
            {
                "apiGroups": [f"training.{OPERATOR_API_GROUP}"],
                "resources": [
                    "workshops",
                    "workshopenvironments",
                    "workshopsessions",
                    "trainingportals",
                ],
                "verbs": ["get", "list", "watch"],
            },
            {
                "apiGroups": [f"training.{OPERATOR_API_GROUP}"],
                "resources": [
                    "workshopenvironments",
                    "workshopsessions",
                ],
                "verbs": ["create", "patch", "delete"],
            },
        ],
    }

    kopf.adopt(cluster_role_body)

    pykube.ClusterRole(api, cluster_role_body).create()

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": f"{RESOURCE_NAME_PREFIX}-training-portal-{portal_namespace}",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{RESOURCE_NAME_PREFIX}-training-portal-{portal_namespace}",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "training-portal",
                "namespace": portal_namespace,
            }
        ],
    }

    kopf.adopt(cluster_role_binding_body)

    pykube.ClusterRoleBinding(api, cluster_role_binding_body).create()

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": "training-portal-security-policy",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{RESOURCE_NAME_PREFIX}-nonroot-security-policy-{portal_namespace}",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "training-portal",
                "namespace": portal_namespace,
            }
        ],
    }

    kopf.adopt(role_binding_body)

    pykube.RoleBinding(api, role_binding_body).create()

    # Allocate a persistent volume for storage of the database.

    persistent_volume_claim_body = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": "training-portal",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": "1Gi"}},
        },
    }

    if STORAGE_CLASS:
        persistent_volume_claim_body["spec"]["storageClassName"] = STORAGE_CLASS

    pykube.PersistentVolumeClaim(api, persistent_volume_claim_body).create()

    # Next create the deployment for the portal web interface.

    portal_image = spec.get("portal", {}).get("image", training_portal_image())

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

    google_tracking_id = (
        spec.get("analytics", {})
        .get("google", {})
        .get("trackingId", GOOGLE_TRACKING_ID)
    )

    image_pull_policy = "IfNotPresent"

    if (
        portal_image.endswith(":main")
        or portal_image.endswith(":master")
        or portal_image.endswith(":develop")
        or portal_image.endswith(":latest")
        or ":" not in portal_image
    ):
        image_pull_policy = "Always"

    config_map_body = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "training-portal",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "data": {
            "logo": portal_logo,
            "theme.js": THEME_PORTAL_SCRIPT,
            "theme.css": THEME_PORTAL_STYLE,
        },
    }

    pykube.ConfigMap(api, config_map_body).create()

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "training-portal",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/portal.services.dashboard": "true",
            },
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": "training-portal"}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {
                    "labels": {
                        "deployment": "training-portal",
                        f"training.{OPERATOR_API_GROUP}/component": "portal",
                        f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                        f"training.{OPERATOR_API_GROUP}/portal.services.dashboard": "true",
                    },
                },
                "spec": {
                    "serviceAccountName": "training-portal",
                    "securityContext": {
                        "fsGroup": STORAGE_GROUP,
                        "supplementalGroups": [STORAGE_GROUP],
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
                                    "name": "OPERATOR_API_GROUP",
                                    "value": OPERATOR_API_GROUP,
                                },
                                {
                                    "name": "RESOURCE_STATUS_KEY",
                                    "value": RESOURCE_STATUS_KEY,
                                },
                                {
                                    "name": "RESOURCE_NAME_PREFIX",
                                    "value": RESOURCE_NAME_PREFIX,
                                },
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
                                    "value": INGRESS_DOMAIN,
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
                                    "value": INGRESS_CLASS,
                                },
                                {
                                    "name": "INGRESS_PROTOCOL",
                                    "value": INGRESS_PROTOCOL,
                                },
                                {
                                    "name": "INGRESS_SECRET",
                                    "value": INGRESS_SECRET,
                                },
                                {
                                    "name": "GOOGLE_TRACKING_ID",
                                    "value": google_tracking_id,
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
                            "persistentVolumeClaim": {"claimName": "training-portal"},
                        },
                        {
                            "name": "config",
                            "configMap": {"name": "training-portal"},
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

    if STORAGE_USER:
        storage_init_container = {
            "name": "storage-permissions-initialization",
            "image": portal_image,
            "imagePullPolicy": image_pull_policy,
            "securityContext": {"runAsUser": 0},
            "command": ["/bin/sh", "-c"],
            "args": [
                f"chown {STORAGE_USER}:{STORAGE_GROUP} /mnt && chmod og+rwx /mnt"
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

    pykube.Deployment(api, deployment_body).create()

    # Finally expose the deployment via a service and ingress route.

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "training-portal",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 8080, "protocol": "TCP", "targetPort": 8080}],
            "selector": {"deployment": "training-portal"},
        },
    }

    pykube.Service(api, service_body).create()

    ingress_body = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "training-portal",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
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
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "training-portal",
                                        "port": {"number": 8080},
                                    }
                                },
                            }
                        ]
                    },
                }
            ]
        },
    }

    if INGRESS_CLASS:
        ingress_body["metadata"]["annotations"][
            "kubernetes.io/ingress.class"
        ] = INGRESS_CLASS

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
                "hosts": [portal_hostname],
                "secretName": INGRESS_SECRET,
            }
        ]

    portal_url = f"{INGRESS_PROTOCOL}://{portal_hostname}"

    pykube.Ingress(api, ingress_body).create()

    # Save away the details of the portal which was created in status.

    return {
        "phase": "Running",
        "namespace": portal_namespace,
        "url": portal_url,
        "credentials": {
            "admin": {"username": admin_username, "password": admin_password},
            "robot": {"username": robot_username, "password": robot_password},
        },
        "clients": {"robot": {"id": robot_client_id, "secret": robot_client_secret}},
    }


@kopf.on.delete(
    f"training.{OPERATOR_API_GROUP}", "v1alpha1", "trainingportals", optional=True
)
def training_portal_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
