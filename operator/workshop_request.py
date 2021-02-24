import os
import random
import string

import kopf
import pykube

from system_profile import operator_ingress_domain, operator_ingress_secret

__all__ = ["workshop_request_create", "workshop_request_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@kopf.on.create("training.eduk8s.io", "v1alpha1", "workshoprequests", id="eduk8s")
def workshop_request_create(name, uid, namespace, spec, patch, logger, **_):
    # The name of the custom resource for requesting a workshop doesn't
    # matter, we are going to generate a uniquely named session custom
    # resource anyway. First lookup up the desired workshop environment
    # and determine if it exists and is valid.

    portal_name = spec.get("portal", {}).get("name", "")

    environment_name = spec["environment"]["name"]

    K8SWorkshopEnvironment = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopEnvironment"
    )

    try:

        environment_instance = K8SWorkshopEnvironment.objects(api).get(
            name=environment_name
        )

    except pykube.exceptions.ObjectDoesNotExist:
        patch["status"] = {"eduk8s": {"phase": "Pending"}}
        raise kopf.TemporaryError(
            f"Cannot find the workshop environment {environment_name}."
        )

    # Check if the request comes from a namespace which is permitted to
    # access the workshop and/or provides the required access token.

    if environment_instance.obj["spec"].get("request"):
        enabled = environment_instance.obj["spec"]["request"].get("enabled", False)

        if not enabled:
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Workshop request not permitted for workshop environment."
            )

        namespaces = environment_instance.obj["spec"]["request"].get("namespaces", [])
        token = environment_instance.obj["spec"]["request"].get("token")

        def _substitute_variables(s):
            return s.replace("$(workshop_namespace)", environment_name)

        namespaces = list(map(_substitute_variables, namespaces))

        if namespaces and namespace not in namespaces:
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"Workshop request not permitted from namespace {namespace}."
            )

        if token and spec["environment"].get("token") != token:
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                "Workshop request requires valid matching access token."
            )

    # Calculate username and password for the session. Use "eduk8s" for
    # username if one not defined and generate a password if neccessary.

    username = "eduk8s"
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

    ingress_protocol = "http"

    default_domain = operator_ingress_domain()
    default_secret = operator_ingress_secret()

    ingress_domain = (
        environment_instance.obj["spec"]
        .get("session", {})
        .get("ingress", {})
        .get("domain", default_domain)
    )

    if ingress_domain == default_domain:
        ingress_secret = default_secret
    else:
        ingress_secret = (
            environment_instance.obj["spec"]
            .get("session", {})
            .get("ingress", {})
            .get("secret", "")
        )

    ingress_secret_instance = None

    if ingress_secret:
        try:
            ingress_secret_instance = pykube.Secret.objects(
                api, namespace=environment_name
            ).get(name=ingress_secret)

        except pykube.exceptions.ObjectDoesNotExist:
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"TLS secret {ingress_secret} is not available for workshop."
            )

        if not ingress_secret_instance.obj["data"].get(
            "tls.crt"
        ) or not ingress_secret_instance.obj["data"].get("tls.key"):
            patch["status"] = {"eduk8s": {"phase": "Pending"}}
            raise kopf.TemporaryError(
                f"TLS secret {ingress_secret} for workshop is not valid."
            )

        ingress_protocol = "https"

    env = environment_instance.obj.get("spec", {}).get("session", {}).get("env", [])

    def _generate_random_session_id(n=5):
        return "".join(
            random.choice("bcdfghjklmnpqrstvwxyz0123456789") for _ in range(n)
        )

    count = 0

    K8SWorkshopSession = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
    )

    while True:
        count += 1

        session_id = _generate_random_session_id()

        session_name = f"{environment_name}-{session_id}"

        session_hostname = f"{session_name}.{ingress_domain}"

        session_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "WorkshopSession",
            "metadata": {
                "name": session_name,
                "labels": {
                    "training.eduk8s.io/portal.name": portal_name,
                    "training.eduk8s.io/environment.name": environment_name,
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
                    "ingress": {"domain": ingress_domain, "secret": ingress_secret},
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

        kopf.append_owner_reference(session_body, owner=environment_instance.obj)

        try:
            K8SWorkshopSession(api, session_body).create()

        except pykube.exceptions.PyKubeError as e:
            if e.code == 409:
                if count >= 20:
                    patch["status"] = {"eduk8s": {"phase": "Failed"}}
                    raise kopf.PermanentError("Unable to generate session.")
                continue

        try:
            session_instance = K8SWorkshopSession.objects(api).get(name=session_name)

        except Exception:
            patch["status"] = {"eduk8s": {"phase": "Failed"}}
            raise kopf.PermanentError("Unable to query back session.")

        break

    return {
        "phase": "Running",
        "url": f"{ingress_protocol}://{session_hostname}",
        "username": username,
        "password": password,
        "session": {
            "kind": "WorkshopSession",
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "name": session_name,
            "uid": session_instance.obj["metadata"]["uid"],
        },
    }


@kopf.on.delete("training.eduk8s.io", "v1alpha1", "workshoprequests")
def workshop_request_delete(name, uid, namespace, spec, status, logger, **_):
    # We need to pull the session details from the status of the request,
    # look it up to see if it still exists, verify we created it, and then
    # delete it.

    session_details = status.get("eduk8s", {}).get("session")

    if not session_details:
        return

    session_name = session_details["name"]

    K8SWorkshopSession = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopSession"
    )

    try:
        session_instance = K8SWorkshopSession.objects(api).get(name=session_name)

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
