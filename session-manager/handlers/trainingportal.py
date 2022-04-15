import pykube
import kopf

from .helpers import xget, image_pull_policy

from .config import (
    OPERATOR_API_GROUP,
    OPERATOR_STATUS_KEY,
    OPERATOR_NAME_PREFIX,
    INGRESS_DOMAIN,
    INGRESS_PROTOCOL,
    INGRESS_SECRET,
    INGRESS_CLASS,
    CLUSTER_STORAGE_CLASS,
    CLUSTER_STORAGE_USER,
    CLUSTER_STORAGE_GROUP,
    GOOGLE_TRACKING_ID,
    THEME_PORTAL_SCRIPT,
    THEME_PORTAL_STYLE,
    PORTAL_ADMIN_USERNAME,
    PORTAL_ADMIN_PASSWORD,
    PORTAL_ROBOT_USERNAME,
    PORTAL_ROBOT_PASSWORD,
    PORTAL_ROBOT_CLIENT_ID,
    PORTAL_ROBOT_CLIENT_SECRET,
    TRAINING_PORTAL_IMAGE,
)

__all__ = ["training_portal_create", "training_portal_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "trainingportals",
    id=OPERATOR_STATUS_KEY,
    timeout=900,
)
def training_portal_create(name, uid, spec, patch, logger, **_):
    # Set name for the portal namespace. The hostname used to access the portal
    # can be overridden, but namespace is always the same.

    portal_name = name
    portal_namespace = f"{portal_name}-ui"

    ingress_hostname = xget(spec, "portal.ingress.hostname")

    if not ingress_hostname:
        portal_hostname = f"{portal_name}-ui.{INGRESS_DOMAIN}"
    elif not "." in ingress_hostname:
        portal_hostname = f"{ingress_hostname}.{INGRESS_DOMAIN}"
    else:
        # If a FQDN is used it must still match the global ingress domain.
        portal_hostname = ingress_hostname

    # Generate an admin password and api credentials for portal management.

    admin_username = xget(
        spec, "portal.credentials.admin.username", PORTAL_ADMIN_USERNAME
    )
    admin_password = xget(
        spec, "portal.credentials.admin.password", PORTAL_ADMIN_PASSWORD
    )

    robot_username = xget(
        spec, "portal.credentials.robot.username", PORTAL_ROBOT_USERNAME
    )
    robot_password = xget(
        spec, "portal.credentials.robot.password", PORTAL_ROBOT_PASSWORD
    )

    robot_client_id = xget(spec, "portal.clients.robot.id", PORTAL_ROBOT_CLIENT_ID)
    robot_client_secret = xget(
        spec, "portal.clients.robot.secret", PORTAL_ROBOT_CLIENT_SECRET
    )

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
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
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

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": f"{OPERATOR_NAME_PREFIX}-training-portal-{portal_namespace}",
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{OPERATOR_NAME_PREFIX}-training-portal",
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
            "name": "training-portal-psp",
            "namespace": portal_namespace,
            "labels": {
                f"training.{OPERATOR_API_GROUP}/component": "portal",
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
            },
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{OPERATOR_NAME_PREFIX}-training-portal-psp",
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

    if CLUSTER_STORAGE_CLASS:
        persistent_volume_claim_body["spec"]["storageClassName"] = CLUSTER_STORAGE_CLASS

    pykube.PersistentVolumeClaim(api, persistent_volume_claim_body).create()

    # Next create the deployment for the portal web interface.

    portal_title = xget(spec, "portal.title", "Workshops")
    portal_password = xget(spec, "portal.password", "")
    portal_index = xget(spec, "portal.index", "")
    portal_logo = xget(spec, "portal.logo", "")

    frame_ancestors = ",".join(xget(spec, "portal.theme.frame.ancestors", []))

    registration_type = xget(spec, "portal.registration.type", "one-step")
    enable_registration = str(xget(spec, "portal.registration.enabled", True)).lower()

    catalog_visibility = xget(spec, "portal.catalog.visibility", "private")

    google_tracking_id = xget(spec, "analytics.google.trackingId", GOOGLE_TRACKING_ID)

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
                        "fsGroup": CLUSTER_STORAGE_GROUP,
                        "supplementalGroups": [CLUSTER_STORAGE_GROUP],
                    },
                    "containers": [
                        {
                            "name": "portal",
                            "image": TRAINING_PORTAL_IMAGE,
                            "imagePullPolicy": image_pull_policy(TRAINING_PORTAL_IMAGE),
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
                                    "name": "OPERATOR_STATUS_KEY",
                                    "value": OPERATOR_STATUS_KEY,
                                },
                                {
                                    "name": "OPERATOR_NAME_PREFIX",
                                    "value": OPERATOR_NAME_PREFIX,
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

    # This hack is to cope with Kubernetes clusters which don't properly set up
    # persistent volume ownership. IBM Kubernetes is one example. The init
    # container runs as root and sets permissions on the storage and ensures it
    # is group writable. Note that this will only work where pod security
    # policies are not enforced. Don't attempt to use it if they are. If they
    # are, this hack should not be required.

    if CLUSTER_STORAGE_USER:
        storage_init_container = {
            "name": "storage-permissions-initialization",
            "image": TRAINING_PORTAL_IMAGE,
            "imagePullPolicy": image_pull_policy,
            "securityContext": {"runAsUser": 0},
            "command": ["/bin/sh", "-c"],
            "args": [
                f"chown {CLUSTER_STORAGE_USER}:{CLUSTER_STORAGE_GROUP} /mnt && chmod og+rwx /mnt"
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
    # Nothing to do here at this point because the owner references will ensure
    # that everything is cleaned up appropriately.

    pass
