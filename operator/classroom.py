import os
import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["classroom_create", "classroom_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "classroomdeployments", id="eduk8s")
def classroom_create(name, spec, logger, **_):
    core_api = kubernetes.client.CoreV1Api()
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # Use the name of the custom resource as the name of the workshop
    # environment.

    environment_name = name

    # The name of the workshop to be deployed can differ and is taken
    # from the specification of the classroom. Lookup the workshop
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
        },
    }

    if not password:
        del environment_body["spec"]["session"]["password"]

    # Make the workshop environment a child of the custom resource for
    # the workshop classroom. This way the whole workshop environment
    # will be automatically deleted when the resource definition for the
    # workshop classroom is deleted and we don't have to clean up
    # anything explicitly.

    kopf.adopt(environment_body)

    environment_instance = custom_objects_api.create_cluster_custom_object(
        "training.eduk8s.io", "v1alpha1", "workshopenvironments", environment_body,
    )

    # Calculate list of attendees which need to create workshop sessions.

    attendees = []

    if spec.get("session"):
        attendees = spec["session"].get("attendees", attendees)

    if not attendees:
        capacity = 0

        if spec.get("session"):
            capacity = int(spec["session"].get("capacity", "0"))

            if capacity:
                attendees = [{"id": f"user{n}"} for n in range(1, capacity + 1)]

    # Create a new workshop session for each attendee in the list.

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

        kopf.append_owner_reference(session_body, owner=environment_instance)

        session_instance = custom_objects_api.create_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopsessions", session_body,
        )

    # Save away the details of the sessions which were created in status.

    return {
        "environment": environment_name,
        "attendees": attendees,
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "classroomdeployments")
def classroom_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
