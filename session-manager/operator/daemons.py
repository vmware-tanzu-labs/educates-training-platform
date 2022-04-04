import logging
import asyncio

import kopf
import pykube

from datetime import datetime, timedelta, timezone
from functools import lru_cache

from config import OPERATOR_NAMESPACE

api = pykube.HTTPClient(pykube.KubeConfig.from_env())

_polling_interval = 60
_resource_timeout = 90

logger = logging.getLogger('educates.operator')

def get_overdue_terminating_session_namespaces(timeout=_resource_timeout):
    label_set = [
        "training.eduk8s.io/component=session",
        "training.eduk8s.io/session.name",
    ]

    selector = ",".join(label_set)

    now = datetime.now(timezone.utc)

    for namespace_item in pykube.Namespace.objects(api).filter(selector=selector):
        if namespace_item.obj["status"]["phase"] == "Terminating":
            if namespace_item.metadata.get("deletionTimestamp"):
                timestamp = namespace_item.metadata["deletionTimestamp"]
                when = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")

                if now - when > timedelta(seconds=timeout):
                    yield namespace_item.name


def api_groups():
    return api.session.get(url=api.url + "/apis").json()["groups"]


def get_all_api_versions():
    # Need to first yield up standard Kubernetes api group.

    yield "v1"

    # Now yield up all additional api groups.

    for group in api_groups():
        name = group["name"]
        for version in group["versions"]:
            yield version["groupVersion"]


@lru_cache(1)
def get_all_namespaced_resources():
    resource_objects = {}

    for api_version in get_all_api_versions():
        resources = api.resource_list(api_version)
        api_version = resources["groupVersion"]
        for resource in resources["resources"]:
            if (
                resource["namespaced"]
                and "get" in resource["verbs"]
                and "/" not in resource["name"]
            ):
                kind = resource["kind"]
                resource_type = pykube.object_factory(api, api_version, kind)
                resource_objects[(api_version, kind)] = resource_type

    return resource_objects


def purge_terminated_resources(namespace):
    logger.info(f"Attempting to purge namespace {namespace}.")
    for resource_type in get_all_namespaced_resources().values():
        for resource in resource_type.objects(api, namespace=namespace).all():
            if resource.metadata.get("deletionTimestamp"):
                if resource.metadata.get("finalizers"):
                    try:
                        logger.info(f"Forcibly deleting finalizers on {resource.obj}.")
                        resource.metadata["finalizers"] = None
                        resource.update()
                    except pykube.exceptions.KubernetesError as e:
                        if e.code != 404:
                            logger.error(
                                f"Could not delete finalizers on {resource.obj}."
                            )


@asyncio.coroutine
def purge_namespaces():
    while True:
        try:
            logger.info("Checking whether namespaces need purging.")
            for namespace in get_overdue_terminating_session_namespaces():
                purge_terminated_resources(namespace)
        except Exception as e:
            logger.error(f"Unexpected error occurred {e}.")

        yield from asyncio.sleep(_polling_interval)


def copy_secret_to_namespace(name, namespace, obj, logger):
    # Lookup the secret to be updated and if can't find it then raise a
    # warning but otherwise ignore it.

    try:
        resource = pykube.Secret.objects(api).filter(namespace=namespace).get(name=name)

    except pykube.exceptions.ObjectDoesNotExist:
        logger.warning(f"Secret {name} in {namespace} doesn't exist.")
        return

    # Don't update if the type of the secret is different.

    if resource.obj["type"] != obj["type"]:
        logger.warning(f"Type of of secret {name} in {namespace} doesn't match.")
        return

    # Don't update if there doesn't appear to be anything which has changed.

    if resource.obj["data"] == obj["data"]:
        return

    # Update the secret.

    resource.obj["data"] = obj["data"]

    try:
        logger.info(f"Updating secret {name} in {namespace}.")
        resource.update()
    except pykube.exceptions.KubernetesError as e:
        logger.error(f"Could not update secret {name} in {namespace}.")


@kopf.on.event("", "v1", "secrets")
def update_secret(type, event, logger, **_):
    obj = event["object"]
    source_name = obj["metadata"]["name"]
    source_namespace = obj["metadata"]["namespace"]

    secret_ref = f"{source_namespace}/{source_name}"

    # If secret already exists, indicated by type being None, the secret is
    # added or modified later, do a full reconcilation to ensure whether
    # secret is now a candidate to copy. Don't care about a secret being
    # deleted.

    if type not in (None, "ADDED", "MODIFIED"):
        return

    # We only care about secrets for ingress or image registries.

    if obj["type"] not in ("kubernetes.io/tls", "kubernetes.io/dockerconfigjson"):
        return

    # Validate that secrets in the correct format for what we need.

    if obj["type"] == "kubernetes.io/tls" and (
        not obj.get("data", {}).get("tls.crt") or not obj.get("data", {}).get("tls.key")
    ):
        return

    if obj["type"] == "kubernetes.io/dockerconfigjson" and not obj.get("data").get(
        ".dockerconfigjson"
    ):
        return

    # Loop over all training portals and look for any which reference the
    # secret.

    K8STrainingPortal = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "TrainingPortal"
    )

    for resource in K8STrainingPortal.objects(api):
        # Ensure that is a training portal resource that has been processed.

        if not resource.obj.get("status", {}).get("eduk8s", {}).get("secrets"):
            continue

        status = resource.obj["status"]["eduk8s"]
        target_namespace = status["namespace"]
        secrets = status["secrets"]

        if secret_ref in secrets["ingress"]:
            copy_secret_to_namespace(source_name, target_namespace, obj, logger)

        if source_name in secrets["registry"]:
            copy_secret_to_namespace(source_name, target_namespace, obj, logger)

    # Loop over all workshop environments and look for any which reference the
    # secret.

    K8SWorkshopEnvironment = pykube.object_factory(
        api, "training.eduk8s.io/v1alpha1", "WorkshopEnvironment"
    )

    for resource in K8SWorkshopEnvironment.objects(api):
        # Ensure that is a training portal resource that has been processed.

        if not resource.obj.get("status", {}).get("eduk8s", {}).get("secrets"):
            continue

        status = resource.obj["status"]["eduk8s"]
        target_namespace = status["namespace"]
        secrets = status["secrets"]

        if secret_ref in secrets["ingress"]:
            copy_secret_to_namespace(source_name, target_namespace, obj, logger)

        if source_name in secrets["registry"]:
            copy_secret_to_namespace(source_name, target_namespace, obj, logger)
