import random
import string

import kopf
import pykube

from .objects import WorkshopEnvironment, WorkshopSession

from .config import (
    OPERATOR_API_GROUP,
    OPERATOR_STATUS_KEY,
    INGRESS_DOMAIN,
    INGRESS_SECRET,
    INGRESS_PROTOCOL
)

__all__ = ["workshop_request_create", "workshop_request_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1alpha1",
    "workshoprequests",
    id=OPERATOR_STATUS_KEY,
)
def workshop_request_create(name, uid, namespace, spec, patch, logger, **_):
    # The name of the custom resource for requesting a workshop doesn't
    # matter, we are going to generate a uniquely named session custom
    # resource anyway. First lookup up the desired workshop environment
    # and determine if it exists and is valid.

    portal_name = spec.get("portal", {}).get("name", "")

    environment_name = spec["environment"]["name"]

    try:
        environment_instance = WorkshopEnvironment.objects(api).get(
            name=environment_name
        )

    except pykube.exceptions.ObjectDoesNotExist:
        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(
            f"Cannot find the workshop environment {environment_name}."
        )

    # Check if the request comes from a namespace which is permitted to
    # access the workshop and/or provides the required access token.

    if environment_instance.obj["spec"].get("request"):
        enabled = environment_instance.obj["spec"]["request"].get("enabled", False)

        if not enabled:
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Workshop request not permitted for workshop environment."
            )

        namespaces = environment_instance.obj["spec"]["request"].get("namespaces", [])
        token = environment_instance.obj["spec"]["request"].get("token")

        def _substitute_variables(s):
            return s.replace("$(workshop_namespace)", environment_name)

        namespaces = list(map(_substitute_variables, namespaces))

        if namespaces and namespace not in namespaces:
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Workshop request not permitted from namespace {namespace}."
            )

        if token and spec["environment"].get("token") != token:
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
            raise kopf.TemporaryError(
                "Workshop request requires valid matching access token."
            )

    # Calculate username and password for the session. Use "educates" for
    # username if one not defined and generate a password if neccessary.

    username = "educates"
    password = None

    if environment_instance.obj["spec"].get("session"):
        username = environment_instance.obj["spec"]["session"].get("username", username)
        password = environment_instance.obj["spec"]["session"].get("password")

    if password is None:
        characters = string.ascii_letters + string.digits
        password = "".join(random.sample(characters, 12))

    # Now loop try to calculate a session ID that has not been used as
    # yet. To do this we need to actually attempt to create the session
    # custom resource and keep trying again if it exists.

    env = environment_instance.obj.get("spec", {}).get("session", {}).get("env", [])

    def _generate_random_session_id(n=5):
        return "".join(
            random.choice("bcdfghjklmnpqrstvwxyz0123456789") for _ in range(n)
        )

    count = 0

    while True:
        count += 1

        session_id = _generate_random_session_id()

        session_name = f"{environment_name}-{session_id}"

        session_hostname = f"{session_name}.{INGRESS_DOMAIN}"

        session_body = {
            "apiVersion": f"training.{OPERATOR_API_GROUP}/v1alpha1",
            "kind": "WorkshopSession",
            "metadata": {
                "name": session_name,
                "labels": {
                    f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                    f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                },
            },
            "spec": {
                "environment": {
                    "name": environment_name,
                },
                "session": {
                    "id": session_id,
                    "username": username,
                    "password": password,
                    "ingress": {
                        "domain": INGRESS_DOMAIN,
                        "secret": INGRESS_SECRET,
                    },
                    "env": env,
                },
                "request": {
                    "namespace": namespace,
                    "kind": "WorkshopRequest",
                    "apiVersion": f"training.{OPERATOR_API_GROUP}/v1alpha1",
                    "name": name,
                    "uid": uid,
                },
            },
        }

        kopf.append_owner_reference(session_body, owner=environment_instance.obj)

        try:
            WorkshopSession(api, session_body).create()

        except pykube.exceptions.PyKubeError as e:
            if e.code == 409:
                if count >= 20:
                    patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Failed"}}
                    raise kopf.PermanentError("Unable to generate session.")
                continue

        try:
            session_instance = WorkshopSession.objects(api).get(name=session_name)

        except Exception:
            patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Failed"}}
            raise kopf.PermanentError("Unable to query back session.")

        break

    return {
        "phase": "Running",
        "url": f"{INGRESS_PROTOCOL}://{session_hostname}",
        "username": username,
        "password": password,
        "session": {
            "kind": "WorkshopSession",
            "apiVersion": f"training.{OPERATOR_API_GROUP}/v1alpha1",
            "name": session_name,
            "uid": session_instance.obj["metadata"]["uid"],
        },
    }


@kopf.on.delete(f"training.{OPERATOR_API_GROUP}", "v1alpha1", "workshoprequests")
def workshop_request_delete(name, uid, namespace, spec, status, logger, **_):
    # We need to pull the session details from the status of the request,
    # look it up to see if it still exists, verify we created it, and then
    # delete it.

    session_details = status.get(OPERATOR_STATUS_KEY, {}).get("session")

    if not session_details:
        return

    session_name = session_details["name"]

    try:
        session_instance = WorkshopSession.objects(api).get(name=session_name)

    except pykube.exceptions.ObjectDoesNotExist:
        return

    request_details = session_instance.obj["spec"].get("request")

    if (
        not request_details
        or request_details.get("namespace") != namespace
        or request_details.get("name") != name
        or request_details.get("uid") != uid
    ):
        return

    try:
        session_instance.delete()

    except pykube.exceptions.ObjectDoesNotExist:
        pass
