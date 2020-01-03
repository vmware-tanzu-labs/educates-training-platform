import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["request_create", "request_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshoprequests")
def request_create(name, namespace, spec, logger, **_):
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

    username = environment_instance["spec"]["session"].get("username", "eduk8s")
    password = environment_instance["spec"]["session"].get("password")

    if password is None:
        password = "-".join(str(random.randint(0, 9999)) for i in range(3))

    # Now loop try to calculate a session ID that has not been used as
    # yet. To do this we need to actually attempt to create the session
    # custom resource and keep trying again if it exists.

    domain = environment_instance["spec"]["session"]["domain"]
    env = environment_instance["spec"]["session"].get("env", [])

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
                "environment": workshop_name,
                "sessionID": session_id,
                "username": username,
                "password": password,
                "domain": domain,
                "env": env,
            },
        }

        kopf.adopt(session_body)

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

    return {"url": f"http://{hostname}", "username": username, "password": password}


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshoprequests")
def request_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
