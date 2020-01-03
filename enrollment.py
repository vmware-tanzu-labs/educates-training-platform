import random
import string

import kopf
import kubernetes
import kubernetes.client
import kubernetes.utils

__all__ = ["enrollment_create", "enrollment_delete"]


@kopf.on.create("training.eduk8s.io", "v1alpha1", "enrollments")
def enrollment_create(name, spec, logger, **_):
    custom_objects_api = kubernetes.client.CustomObjectsApi()

    # The name of the enrollment custom resource doesn't matter, we are
    # going to generate a uniquely named session custom resource in the
    # namespace for the workshop. First lookup up the desired workshop
    # and determine if it exists and is valid. The workspace custom
    # resources exist in the "eduk8s" namespace where the operator runs.

    workspace_name = spec["workspace"]

    try:
        workspace_instance = custom_objects_api.get_cluster_custom_object(
            "training.eduk8s.io", "v1alpha1", "workspaces", workspace_name
        )
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            raise kopf.PermanentError(f"Cannot find a workshop {workspace_name}.")

    # Calculate username and password for the session. Use "eduk8s" for
    # username if one not defined and generate a password if neccessary.

    username = workspace_instance["spec"].get("username", "eduk8s")
    password = workspace_instance["spec"].get("password")

    if password is None:
        password = "-".join(str(random.randint(0, 9999)) for i in range(3))

    # Now loop try to calculate a user ID that has been used as yet. To
    # do this we need to actually attempt to create the session custom
    # resource and try and again if it exists.

    domain = workspace_instance["spec"]["domain"]
    env = workspace_instance["spec"].get("env", [])

    random_userid_chars = "bcdfghjklmnpqrstvwxyz0123456789"

    def _generate_random_userid(n=5):
        return "".join(random.choice(random_userid_chars) for _ in range(n))

    count = 0

    while True:
        count += 1

        user_id = _generate_random_userid()

        session_name = f"{workspace_name}-{user_id}"

        hostname = f"{session_name}.{domain}"

        session_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "Session",
            "metadata": {"name": session_name},
            "spec": {
                "userID": user_id,
                "workspace": workspace_name,
                "username": username,
                "password": password,
                "domain": domain,
                "env": env,
            },
        }

        kopf.adopt(session_body)

        try:
            session_instance = custom_objects_api.create_cluster_custom_object(
                "training.eduk8s.io",
                "v1alpha1",
                "sessions",
                session_body,
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


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "enrollments")
def enrollment_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    return {}
