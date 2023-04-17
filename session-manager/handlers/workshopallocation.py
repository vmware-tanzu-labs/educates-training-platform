import base64

import kopf
import pykube

from .objects import create_from_dict
from .helpers import xget, substitute_variables
from .analytics import report_analytics_event


from .operator_config import (
    OPERATOR_API_GROUP,
    OPERATOR_STATUS_KEY,
)

__all__ = ["workshop_allocation_create", "workshop_allocation_delete"]

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


@kopf.index(
    "",
    "v1",
    "secrets",
    labels={
        f"training.{OPERATOR_API_GROUP}/component": "session",
        f"training.{OPERATOR_API_GROUP}/component.group": "variables",
    },
)
def session_variables_secret_index(
    namespace,
    name,
    body,
    **_,
):
    return {(namespace, name): body.get("data", {})}


@kopf.index(
    "",
    "v1",
    "secrets",
    labels={
        f"training.{OPERATOR_API_GROUP}/component": "request",
        f"training.{OPERATOR_API_GROUP}/component.group": "variables",
    },
)
def request_variables_secret_index(
    namespace,
    name,
    body,
    **_,
):
    return {(namespace, name): body.get("data", {})}


@kopf.on.create(
    f"training.{OPERATOR_API_GROUP}",
    "v1beta1",
    "workshopallocations",
    id=OPERATOR_STATUS_KEY,
)
def workshop_allocation_create(
    name,
    uid,
    meta,
    spec,
    status,
    patch,
    logger,
    runtime,
    retry,
    workshop_environment_index,
    workshop_session_index,
    session_variables_secret_index,
    request_variables_secret_index,
    **_,
):
    # Check whether we have cached copy of workshop environment and request
    # parameters secret.

    portal_name = meta.get("labels", {}).get(
        f"training.{OPERATOR_API_GROUP}/portal.name", ""
    )

    environment_name = spec["environment"]["name"]
    workshop_namespace = environment_name
    session_name = spec["session"]["name"]
    session_namespace = session_name
    variables_name = f"{session_name}-session"
    parameters_name = f"{session_name}-request"

    if not (None, environment_name) in workshop_environment_index:
        if runtime.total_seconds() >= 30:
            patch["status"] = {
                OPERATOR_STATUS_KEY: {
                    "phase": "Failed",
                    "message": f"Workshop environment {environment_name} is not available.",
                }
            }

            report_analytics_event(
                "Resource/PermanentError",
                {
                    "kind": "WorkshopAllocation",
                    "name": name,
                    "uid": uid,
                    "retry": retry,
                    "message": f"Workshop environment {environment_name} is not available.",
                },
            )

            raise kopf.PermanentError(
                f"Workshop environment {environment_name} is not available."
            )

        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(
            f"No record of workshop environment {environment_name}.", delay=5
        )

    environment_instance, *_ = workshop_environment_index[(None, environment_name)]

    if not (None, session_name) in workshop_session_index:
        if runtime.total_seconds() >= 30:
            patch["status"] = {
                OPERATOR_STATUS_KEY: {
                    "phase": "Failed",
                    "message": f"Workshop session {session_name} is not available.",
                }
            }

            report_analytics_event(
                "Resource/PermanentError",
                {
                    "kind": "WorkshopAllocation",
                    "name": name,
                    "uid": uid,
                    "retry": retry,
                    "message": f"Workshop session {session_name} is not available.",
                },
            )

            raise kopf.PermanentError(
                f"Workshop session {session_name} is not available."
            )

        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(
            f"No record of workshop session {session_name}.", delay=5
        )

    session_instance, *_ = workshop_session_index[(None, session_name)]

    if not (workshop_namespace, variables_name) in session_variables_secret_index:
        if runtime.total_seconds() >= 30:
            patch["status"] = {
                OPERATOR_STATUS_KEY: {
                    "phase": "Failed",
                    "message": f"Variables secret {variables_name} is not available.",
                }
            }

            report_analytics_event(
                "Resource/PermanentError",
                {
                    "kind": "WorkshopAllocation",
                    "name": name,
                    "uid": uid,
                    "retry": retry,
                    "message": f"Variables secret {variables_name} is not available.",
                },
            )

            raise kopf.PermanentError(
                f"Variables secret {variables_name} is not available."
            )

        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(
            f"No record of variables secret {variables_name}.", delay=5
        )

    variables_data, *_ = session_variables_secret_index[
        (workshop_namespace, variables_name)
    ]

    if not (workshop_namespace, parameters_name) in request_variables_secret_index:
        if runtime.total_seconds() >= 30:
            patch["status"] = {
                OPERATOR_STATUS_KEY: {
                    "phase": "Failed",
                    "message": f"Parameters secret {parameters_name} is not available.",
                }
            }

            report_analytics_event(
                "Resource/PermanentError",
                {
                    "kind": "WorkshopAllocation",
                    "name": name,
                    "uid": uid,
                    "retry": retry,
                    "message": f"Parameters secret {parameters_name} is not available.",
                },
            )

            raise kopf.PermanentError(
                f"Parameters secret {parameters_name} is not available."
            )

        patch["status"] = {OPERATOR_STATUS_KEY: {"phase": "Pending"}}
        raise kopf.TemporaryError(
            f"No record of parameters secret {parameters_name}.", delay=5
        )

    parameters_data, *_ = request_variables_secret_index[
        (workshop_namespace, parameters_name)
    ]

    session_variables = {}

    for key, value in parameters_data.items():
        session_variables[key] = base64.b64decode(value.encode("UTF-8")).decode("UTF-8")

    for key, value in variables_data.items():
        session_variables[key] = base64.b64decode(value.encode("UTF-8")).decode("UTF-8")

    workshop_name = environment_instance["status"][OPERATOR_STATUS_KEY]["workshop"][
        "name"
    ]

    workshop_spec = environment_instance["status"][OPERATOR_STATUS_KEY]["workshop"][
        "spec"
    ]

    objects = []

    if workshop_spec.get("request"):
        objects.extend(workshop_spec["request"].get("objects", []))

    for object_body in objects:
        object_body = substitute_variables(object_body, session_variables)

        if not object_body["metadata"].get("namespace"):
            object_body["metadata"]["namespace"] = session_namespace

        object_body["metadata"].setdefault("labels", {}).update(
            {
                f"training.{OPERATOR_API_GROUP}/component": "request",
                f"training.{OPERATOR_API_GROUP}/component.group": "objects",
                f"training.{OPERATOR_API_GROUP}/workshop.name": workshop_name,
                f"training.{OPERATOR_API_GROUP}/portal.name": portal_name,
                f"training.{OPERATOR_API_GROUP}/environment.name": environment_name,
                f"training.{OPERATOR_API_GROUP}/session.name": session_name,
                f"training.{OPERATOR_API_GROUP}/session.objects": "true",
            }
        )

        kopf.adopt(object_body)

        try:
            create_from_dict(object_body)

        except pykube.exceptions.KubernetesError as e:
            logger.exception(
                f"Unable to create workshop request objects for session {session_namespace}."
            )

            patch["status"] = {
                OPERATOR_STATUS_KEY: {
                    "phase": "Failed",
                    "message": "Unable to create workshop request objects for session",
                }
            }

            raise kopf.PermanentError(
                f"Unable to create workshop request objects for session {session_namespace}."
            )

    return {
        "phase": "Allocated",
        "message": None,
    }


@kopf.on.delete(
    f"training.{OPERATOR_API_GROUP}", "v1beta1", "workshopallocations", optional=True
)
def workshop_allocation_delete(name, spec, logger, **_):
    # Nothing to do here at this point because the owner references will
    # ensure that everything is cleaned up appropriately.

    pass
