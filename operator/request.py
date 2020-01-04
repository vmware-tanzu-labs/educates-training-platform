import os
import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["request_create", "request_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshoprequests")
def request_create(name, uid, namespace, spec, logger, **_):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # The name of the custom resource for requesting a workshop doesn't
    # matter, we are going to generate a uniquely named session custom
    # resource anyway. First lookup up the desired workshop environment
    # and determine if it exists and is valid.

    workshop_name = spec["environment"]

    try:
        environment_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopenvironments", workshop_name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise kopf.TemporaryError(
                f"Cannot find a workshop environment {workshop_name}."
            )

    # Check if the request comes from a namespace which is permitted to
    # access the workshop and/or provides the required access token.

    if environment_instance["spec"].get("request"):
        namespaces = environment_instance["spec"]["request"].get("namespaces")
        token = environment_instance["spec"]["request"].get("token")

        if namespaces and namespace not in namespaces:
            raise kopf.TemporaryError(
                f"Workshop request not permitted from namespace {namespace}."
            )

        if token and spec.get("token") != token:
            raise kopf.TemporaryError(
                f"Workshop request requires valid matching access token."
            )

    # Calculate username and password for the session. Use "eduk8s" for
    # username if one not defined and generate a password if neccessary.

    username = "eduk8s"
    password = None

    if environment_instance["spec"].get("session"):
        username = environment_instance["spec"]["session"].get("username", username)
        password = environment_instance["spec"]["session"].get("password")

    if password is None:
        password = "-".join(str(random.randint(0, 9999)) for i in range(3))

    # Now loop try to calculate a session ID that has not been used as
    # yet. To do this we need to actually attempt to create the session
    # custom resource and keep trying again if it exists.

    domain = os.environ.get("INGRESS_DOMAIN", "training.eduk8s.io")
    env = []

    if environment_instance["spec"].get("session"):
        domain = environment_instance["spec"]["session"].get("domain", domain)
        env = environment_instance["spec"]["session"].get("env", env)

    def _generate_random_session_id(n=5):
        return "".join(
            random.choice("bcdfghjklmnpqrstvwxyz0123456789") for _ in range(n)
        )

    count = 0

    while True:
        count += 1

        session_id = _generate_random_session_id()

        session_name = f"{workshop_name}-{session_id}"

        hostname = f"{session_name}.{domain}"

        session_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "WorkshopSession",
            "metadata": {"name": session_name},
            "spec": {
                "environment": {"name": workshop_name,},
                "session": {
                    "id": session_id,
                    "username": username,
                    "password": password,
                    "domain": domain,
                    "env": env,
                },
                "request": {
                    "namespace": namespace,
                    "kind": "WorkshopRequest",
                    "apiVersion": "training.eduk8s.io/v1alpha1",
                    "name": name,
                    "uid": uid,
                },
            },
        }

        kopf.append_owner_reference(session_body, owner=environment_instance)

        try:
            session_instance = custom_objects_api.create_cluster_custom_object(
                "training.eduk8s.io", "v1alpha1", "workshopsessions", session_body,
            )
        except kubernetes.client.rest.ApiException as e:
            if e.status == 409:
                if count >= 20:
                    raise kopf.TemporaryError("Unable to generate session.")
                continue
            else:
                raise

        break

    return {
        "url": f"http://{hostname}",
        "username": username,
        "password": password,
        "session": {
            "kind": "WorkshopSession",
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "name": session_name,
            "uid": session_instance["metadata"]["uid"],
        },
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshoprequests")
def request_delete(name, uid, namespace, spec, status, logger, **_):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # We need to pull the session details from the status of the request,
    # look it up to see if it still exists, verify we created it, and then
    # delete it.

    session_details = status["request_create"]["session"]

    session_name = session_details["name"]

    try:
        session_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workshopsessions", session_name,
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            return
        raise

    request_details = session_instance["spec"].get("request")

    if (
        not request_details
        or request_details.get("namespace") != namespace
        or request_details.get("name") != name
        or request_details.get("uid") != uid
    ):
        return

    try:
        custom_objects_api.delete_cluster_custom_object(
            "training.eduk8s.io",
            "v1alpha1",
            "workshopsessions",
            session_name,
            kubernetes.client.V1DeleteOptions(),
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            pass
        raise
