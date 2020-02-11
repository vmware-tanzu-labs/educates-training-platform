import os
import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["training_portal_create", "training_portal_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "trainingportals", id="eduk8s")
def training_portal_create(name, spec, logger, **_):
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # Use the name of the custom resource as the name of the workshop
    # environment.

    environment_name = name
    workshop_namespace = environment_name

    # The name of the workshop to be deployed can differ and is taken
    # from the specification of the training portal. Lookup the workshop
    # resource definition and ensure it exists.

    workshop_name = spec["workshop"]["name"]

    try:
        workshop_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshops", workshop_name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise kopf.TemporaryError(f"Workshop {workshop_name} is not available.")

    # Calculate username and password for the session. Use "eduk8s" for
    # username if one not defined and generate a password if neccessary.
    # Also generate a token for use in workshop requests if needed.

    username = "eduk8s"
    password = None

    if spec.get("session"):
        username = spec["session"].get("username", username)
        password = spec["session"].get("password")

    characters = string.ascii_letters + string.digits

    token = "".join(random.sample(characters, 32))

    # Defined the body of the workshop environment to be created.

    domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
    env = []

    if spec.get("session"):
        domain = spec["session"].get("domain", domain)
        env = spec["session"].get("env", env)

    environment_body = {
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "kind": "WorkshopEnvironment",
        "metadata": {"name": environment_name},
        "spec": {
            "workshop": {"name": workshop_name},
            "request": {"token": token, "namespaces": [environment_name]},
            "session": {
                "username": username,
                "password": password,
                "domain": domain,
                "env": env,
            },
            "environment": {"objects": [],},
        },
    }

    if not password:
        del environment_body["spec"]["session"]["password"]

    # Calculate list of attendees which need to create workshop sessions.

    attendees = []

    if spec.get("session"):
        attendees = spec["session"].get("attendees", attendees)

    if not attendees:
        capacity = 1

        if spec.get("session"):
            capacity = int(spec["session"].get("capacity", "1"))

            if capacity:
                attendees = [{"id": f"user{n}"} for n in range(1, capacity + 1)]

    # Create a new workshop session for each attendee in the list. We
    # add this to the workshop environment as a resource object to be
    # created later when the workshop environment is created.

    for attendee in attendees:
        session_id = attendee["id"]
        session_name = f"{environment_name}-{session_id}"

        if not attendee.get("username"):
            attendee["username"] = username
        if not attendee.get("password"):
            attendee["password"] = password or "".join(random.sample(characters, 16))

        attendee["hostname"] = f"{session_name}.{domain}"

        session_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "WorkshopSession",
            "metadata": {
                "name": session_name,
                "labels": {"workshop-environment": environment_name,},
            },
            "spec": {
                "environment": {"name": environment_name,},
                "session": {
                    "id": session_id,
                    "username": attendee["username"],
                    "password": attendee["password"],
                    "hostname": attendee["hostname"],
                    "env": attendee.get("env", []),
                },
            },
        }

        environment_body["spec"]["environment"]["objects"].append(session_body)

    # Add resources to deploy interface for accessing workshop instances.

    portal_hostname = f"{environment_name}.{domain}"

    interface_resources = [
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "eduk8s-portal"},
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"name": "eduk8s-portal"},
            "rules": [
                {
                    "apiGroups": ["training.eduk8s.io"],
                    "resources": ["workshopsessions"],
                    "verbs": ["get", "list"],
                }
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {"name": "eduk8s-portal"},
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": "eduk8s-portal",
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": "eduk8s-portal",
                    "namespace": workshop_namespace,
                }
            ],
        },
        {
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
                                "image": "quay.io/eduk8s/eduk8s-portal:master",
                                "imagePullPolicy": "Always",
                                "resources": {
                                    "requests": {"memory": "256Mi"},
                                    "limits": {"memory": "256Mi"},
                                },
                                "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                            }
                        ],
                    },
                },
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "eduk8s-portal"},
            "spec": {
                "type": "ClusterIP",
                "ports": [{"port": 8080, "protocol": "TCP", "targetPort": 8080}],
                "selector": {"deployment": "eduk8s-portal"},
            },
        },
        {
            "apiVersion": "extensions/v1beta1",
            "kind": "Ingress",
            "metadata": {"name": "eduk8s-portal"},
            "spec": {
                "rules": [
                    {
                        "host": f"{environment_name}.{domain}",
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
        },
    ]

    environment_body["spec"]["environment"]["objects"].extend(interface_resources)

    # Make the workshop environment a child of the custom resource for
    # the training portal. This way the whole workshop environment will be
    # automatically deleted when the resource definition for the
    # training portal is deleted and we don't have to clean up anything
    # explicitly.

    kopf.adopt(environment_body)

    custom_objects_api.create_cluster_custom_object(
        "training.eduk8s.io", "v1alpha1", "workshopenvironments", environment_body,
    )

    # Save away the details of the sessions which were created in status.

    return {
        "environment": environment_name,
        "portal": f"http://{portal_hostname}",
        "attendees": attendees,
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "trainingportals", optional=True)
def training_portal_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
