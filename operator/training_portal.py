import os
import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

from system_profile import operator_ingress_domain, operator_ingress_secret

__all__ = ["training_portal_create", "training_portal_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "trainingportals", id="eduk8s")
def training_portal_create(name, spec, logger, **_):
    apps_api = kubernetes.client.AppsV1Api()
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    extensions_api = kubernetes.client.ExtensionsV1beta1Api()
    rbac_authorization_api = kubernetes.client.RbacAuthorizationV1Api()

    # Before we do anything, verify that the workshops listed in the
    # specification already exist. Don't continue unless they do.

    workshop_instances = {}

    for n, workshop in enumerate(spec.get("workshops", [])):
        # Use the name of the custom resource as the name of the workshop
        # environment.

        workshop_name = workshop["name"]

        # Verify that the workshop definition exists.

        try:
            workshop_instance = custom_objects_api.get_cluster_custom_object(
                "training.eduk8s.io", "v1alpha2", "workshops", workshop_name
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise kopf.TemporaryError(f"Workshop {workshop_name} is not available.")
            raise

        workshop_instances[workshop_name] = workshop_instance

    # Use the name of the custom resource with prefix "eduk8s-" as the
    # name of the portal namespace.

    portal_name = name
    portal_namespace = f"{portal_name}-ui"

    # Determine URL to be used for accessing the portal web interface.

    ingress_protocol = "http"

    default_domain = operator_ingress_domain()
    default_secret = operator_ingress_secret()

    ingress_hostname = spec.get("portal", {}).get("ingress", {}).get("hostname")

    ingress_domain = (
        spec.get("portal", {}).get("ingress", {}).get("domain", default_domain)
    )

    if not ingress_hostname:
        portal_hostname = f"{portal_name}-ui.{ingress_domain}"
    elif not "." in ingress_hostname:
        portal_hostname = f"{ingress_hostname}.{ingress_domain}"
    else:
        portal_hostname = ingress_hostname

    if ingress_domain == default_domain:
        ingress_secret = default_secret
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

        if not ingress_secret_instance.data.get(
            "tls.crt"
        ) or not ingress_secret_instance.data.get("tls.key"):
            raise kopf.TemporaryError(f"TLS secret {ingress_secret} is not valid.")

        ingress_protocol = "https"

    # Generate an admin password and api credentials for portal management.

    characters = string.ascii_letters + string.digits

    credentials = spec.get("portal", {}).get("credentials", {})

    admin_credentials = credentials.get("admin", {})
    robot_credentials = credentials.get("robot", {})

    clients = spec.get("portal", {}).get("clients", {})

    robot_client = clients.get("robot", {})

    admin_username = admin_credentials.get("username", "eduk8s")

    admin_password = "".join(random.sample(characters, 32))
    admin_password = admin_credentials.get("password", admin_password)

    robot_username = robot_credentials.get("username", "robot@eduk8s")

    robot_password = "".join(random.sample(characters, 32))
    robot_password = robot_credentials.get("password", robot_password)

    robot_client_id = "".join(random.sample(characters, 32))
    robot_client_id = robot_client.get("id", robot_client_id)

    robot_client_secret = "".join(random.sample(characters, 32))
    robot_client_secret = robot_client.get("secret", robot_client_secret)

    # Create the namespace for holding the web interface for the portal.

    namespace_body = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": portal_namespace},
    }

    # Make the namespace for the portal a child of the custom resource
    # for the training portal. This way the namespace will be
    # automatically deleted when the resource definition for the
    # training portal is deleted and we don't have to clean up anything
    # explicitly.

    kopf.adopt(namespace_body)

    namespace_instance = core_api.create_namespace(body=namespace_body)

    # Delete any limit ranges applied to the namespace so they don't
    # cause issues with deploying the training portal.

    limit_ranges = core_api.list_namespaced_limit_range(namespace=portal_namespace)

    for limit_range in limit_ranges.items:
        core_api.delete_namespaced_limit_range(
            namespace=portal_namespace, name=limit_range["metadata"]["name"]
        )

    # Delete any resource quotas applied to the namespace so they don't
    # cause issues with deploying the training portal.

    resource_quotas = core_api.list_namespaced_resource_quota(
        namespace=portal_namespace
    )

    for resource_quota in resource_quotas.items:
        core_api.delete_namespaced_resource_quota(
            namespace=portal_namespace, name=resource_quota["metadata"]["name"]
        )

    # Make a copy of the TLS secret into the portal namespace.

    if ingress_secret:
        secret_body = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": ingress_secret},
            "type": "kubernetes.io/tls",
            "data": {
                "tls.crt": ingress_secret_instance.data["tls.crt"],
                "tls.key": ingress_secret_instance.data["tls.key"],
            },
        }

        core_api.create_namespaced_secret(namespace=portal_namespace, body=secret_body)

    # Now need to loop over the list of the workshops and create the
    # workshop environment and required number of sessions for each.

    workshops = []
    environments = []

    default_capacity = spec.get("portal", {}).get("capacity", 0)
    default_reserved = spec.get("portal", {}).get("reserved", default_capacity)
    default_initial = spec.get("portal", {}).get("initial", default_reserved)

    default_expires = spec.get("portal", {}).get("expires", "0m")
    default_orphaned = spec.get("portal", {}).get("orphaned", "0m")

    for n, workshop in enumerate(spec.get("workshops", [])):
        # Use the name of the custom resource as the name of the workshop
        # environment.

        workshop_name = workshop["name"]
        environment_name = f"{portal_name}-w{n+1:02}"

        workshop_instance = workshop_instances[workshop_name]

        workshop_details = {
            "name": workshop_name,
            "title": workshop_instance.get("spec", {}).get("title", ""),
            "description": workshop_instance.get("spec", {}).get("description", ""),
            "vendor": workshop_instance.get("spec", {}).get("vendor", ""),
            "authors": workshop_instance.get("spec", {}).get("authors", []),
            "difficulty": workshop_instance.get("spec", {}).get("difficulty", ""),
            "duration": workshop_instance.get("spec", {}).get("duration", ""),
            "tags": workshop_instance.get("spec", {}).get("tags", []),
            "logo": workshop_instance.get("spec", {}).get("logo", ""),
            "url": workshop_instance.get("spec", {}).get("url", ""),
            "content": workshop_instance.get("spec", {}).get("content", {}),
        }

        workshops.append(workshop_details)

        # Defined the body of the workshop environment to be created.

        env = workshop.get("env", [])

        environment_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "WorkshopEnvironment",
            "metadata": {"name": environment_name,},
            "spec": {
                "workshop": {"name": workshop_name},
                "request": {"namespaces": ["--requests-disabled--"]},
                "session": {
                    "ingress": {"domain": ingress_domain, "secret": ingress_secret,},
                    "env": env,
                },
                "environment": {"objects": [],},
            },
        }

        # Make the workshop environment a child of the custom resource for
        # the training portal. This way the whole workshop environment will be
        # automatically deleted when the resource definition for the
        # training portal is deleted and we don't have to clean up anything
        # explicitly.

        kopf.adopt(environment_body)

        custom_objects_api.create_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopenvironments", environment_body,
        )

        if workshop.get("capacity") is not None:
            workshop_capacity = workshop.get("capacity", default_capacity)
            workshop_reserved = workshop.get("reserved", workshop_capacity)
            workshop_initial = workshop.get("initial", workshop_reserved)
        else:
            workshop_capacity = default_capacity
            workshop_reserved = default_reserved
            workshop_initial = default_initial

        workshop_capacity = max(0, workshop_capacity)
        workshop_reserved = max(0, min(workshop_reserved, workshop_capacity))
        workshop_initial = max(0, min(workshop_initial, workshop_capacity))

        if workshop_initial < workshop_reserved:
            workshop_initial = workshop_reserved

        workshop_expires = workshop.get("expires", default_expires)
        workshop_orphaned = workshop.get("orphaned", default_orphaned)

        environments.append(
            {
                "name": environment_name,
                "workshop": {"name": workshop_name},
                "capacity": workshop_capacity,
                "initial": workshop_initial,
                "reserved": workshop_reserved,
                "expires": workshop_expires,
                "orphaned": workshop_orphaned,
            }
        )

    # Deploy the training portal web interface. First up need to create a
    # service account and binding required roles to it.

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": "eduk8s-portal"},
    }

    core_api.create_namespaced_service_account(
        namespace=portal_namespace, body=service_account_body
    )

    cluster_role_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {"name": f"eduk8s-portal-{portal_name}"},
        "rules": [
            {
                "apiGroups": ["training.eduk8s.io"],
                "resources": [
                    "workshops",
                    "workshopenvironments",
                    "workshopsessions",
                    "workshoprequests",
                    "trainingportals",
                ],
                "verbs": ["get", "list"],
            },
            {
                "apiGroups": ["training.eduk8s.io"],
                "resources": ["workshopsessions",],
                "verbs": ["create", "delete"],
            },
        ],
    }

    kopf.adopt(cluster_role_body)

    rbac_authorization_api.create_cluster_role(body=cluster_role_body)

    cluster_role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {"name": f"eduk8s-portal-{portal_name}"},
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"eduk8s-portal-{portal_name}",
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

    # Allocate a persistent volume for storage of the database.

    persistent_volume_claim_body = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": "eduk8s-portal"},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": "1Gi"}},
        },
    }

    core_api.create_namespaced_persistent_volume_claim(
        namespace=portal_namespace, body=persistent_volume_claim_body
    )

    # Next create the deployment for the portal web interface.

    portal_image = spec.get("portal", {}).get(
        "image", "quay.io/eduk8s/eduk8s-portal:master"
    )

    registration_type = (
        spec.get("portal", {}).get("registration", {}).get("type", "one-step")
    )

    enable_registration = str(
        spec.get("portal", {}).get("registration", {}).get("enabled", True)
    ).lower()

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "eduk8s-portal"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": "eduk8s-portal"}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {"labels": {"deployment": "eduk8s-portal"}},
                "spec": {
                    "serviceAccountName": "eduk8s-portal",
                    "containers": [
                        {
                            "name": "portal",
                            "image": portal_image,
                            "imagePullPolicy": "Always",
                            "resources": {
                                "requests": {"memory": "256Mi"},
                                "limits": {"memory": "256Mi"},
                            },
                            "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                            "env": [
                                {"name": "TRAINING_PORTAL", "value": portal_name,},
                                {"name": "PORTAL_HOSTNAME", "value": portal_hostname,},
                                {"name": "ADMIN_USERNAME", "value": admin_username,},
                                {"name": "ADMIN_PASSWORD", "value": admin_password,},
                                {"name": "INGRESS_DOMAIN", "value": ingress_domain,},
                                {
                                    "name": "REGISTRATION_TYPE",
                                    "value": registration_type,
                                },
                                {
                                    "name": "ENABLE_REGISTRATION",
                                    "value": enable_registration,
                                },
                                {
                                    "name": "INGRESS_PROTOCOL",
                                    "value": ingress_protocol,
                                },
                                {"name": "INGRESS_SECRET", "value": ingress_secret,},
                            ],
                            "volumeMounts": [
                                {"name": "data", "mountPath": "/var/run/eduk8s"}
                            ],
                        }
                    ],
                    "volumes": [
                        {
                            "name": "data",
                            "persistentVolumeClaim": {"claimName": "eduk8s-portal"},
                        }
                    ],
                },
            },
        },
    }

    apps_api.create_namespaced_deployment(
        namespace=portal_namespace, body=deployment_body
    )

    # Finally expose the deployment via a service and ingress route.

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "eduk8s-portal"},
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
        "metadata": {"name": "eduk8s-portal"},
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

    if ingress_secret:
        ingress_body["spec"]["tls"] = [
            {"hosts": [f"*.{ingress_domain}"], "secretName": ingress_secret,}
        ]

    portal_url = f"{ingress_protocol}://{portal_hostname}"

    extensions_api.create_namespaced_ingress(
        namespace=portal_namespace, body=ingress_body
    )

    # Save away the details of the portal which was created in status.

    return {
        "url": portal_url,
        "credentials": {
            "admin": {"username": admin_username, "password": admin_password},
            "robot": {"username": robot_username, "password": robot_password},
        },
        "clients": {"robot": {"id": robot_client_id, "secret": robot_client_secret}},
        "workshops": workshops,
        "environments": environments,
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "trainingportals", optional=True)
def training_portal_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
