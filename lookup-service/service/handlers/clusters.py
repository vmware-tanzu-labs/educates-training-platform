"""Operator handlers for cluster configuration resources."""

import base64
import logging

from typing import Any, Dict

import kopf
import yaml

from ..service import ServiceState
from ..caches.clusters import ClusterConfiguration
from ..caches.portals import PortalState, PortalAuth
from ..caches.workshops import WorkshopDetails
from ..helpers.objects import xgetattr
from ..helpers.kubeconfig import (
    create_kubeconfig_from_access_token_secret,
    verify_kubeconfig_format,
    extract_context_from_kubeconfig,
)
from ..helpers.operator import GenericOperator


logger = logging.getLogger("educates")


@kopf.index("secrets", when=lambda body, **_: body.get("type") == "Opaque")
def secrets_index(namespace: str, name: str, body: kopf.Body, **_) -> dict:
    """Keeps an index of secret data by namespace and name. This is so we can
    easily retrieve the kubeconfig data for each cluster when starting the
    training platform operator."""

    # Note that under normal circumstances only a single namespace should be
    # monitored, thus we are not caching secrets from the whole cluster but
    # only where the operator is deployed. This is to avoid potential security
    # issues and memory bloat from caching secrets from the whole cluster.

    return {(namespace, name): xgetattr(body, "data", {})}


@kopf.on.resume("clusterconfigs.lookup.educates.dev")
@kopf.on.create("clusterconfigs.lookup.educates.dev")
@kopf.on.update("clusterconfigs.lookup.educates.dev")
def clusterconfigs_update(
    namespace: str,
    name: str,
    uid: str,
    meta: kopf.Meta,
    spec: kopf.Spec,
    secrets_index: Dict[str, Any],
    memo: ServiceState,
    reason: str,
    retry: int,
    **_,
):  # pylint: disable=redefined-outer-name
    """Add the cluster configuration to the cluster database."""

    generation = meta.get("generation")

    # We need to cache the kubeconfig data. This can be provided in a separate
    # secret or it can be read from a mounted secret for the case of the local
    # cluster.

    secret_ref_name = xgetattr(spec, "credentials.kubeconfig.secretRef.name")

    if secret_ref_name is not None:
        config_key = xgetattr(spec, "credentials.kubeconfig.secretRef.key", "config")

        # Make sure the secret holding the kubeconfig has been seen already and
        # that the key for the kubeconfig file is present in the data.

        if (namespace, secret_ref_name) not in secrets_index:
            raise kopf.TemporaryError(
                f"Secret {secret_ref_name} required for cluster configuration {name} not found.",
                delay=5,
            )

        cluster_config_data, *_ = secrets_index[(namespace, secret_ref_name)]

        if config_key not in cluster_config_data:
            raise kopf.TemporaryError(
                f"Key {config_key} not found in secret {secret_ref_name} required for cluster configuration {name}.",  # pylint: disable=line-too-long
                delay=5 if not retry else 15,
            )

        # Decode the base64 encoded kubeconfig data and load it as a yaml
        # document.

        try:
            kubeconfig = yaml.safe_load(
                base64.b64decode(
                    xgetattr(cluster_config_data, config_key, "").encode("UTF-8")
                )
            )
        except yaml.YAMLError as exc:
            raise kopf.TemporaryError(
                f"Failed to load kubeconfig data from secret {secret_ref_name} required for cluster configuration {name}.",  # pylint: disable=line-too-long
                delay=5 if not retry else 15,
            ) from exc

        try:
            verify_kubeconfig_format(kubeconfig)
        except ValueError as exc:
            raise kopf.TemporaryError(
                f"Invalid kubeconfig data in secret {secret_ref_name} required for cluster configuration {name}.",  # pylint: disable=line-too-long
                delay=5 if not retry else 15,
            ) from exc

        # Extract only the context from the kubeconfig file that is required
        # for the cluster configuration.

        try:
            kubeconfig = extract_context_from_kubeconfig(
                kubeconfig, xgetattr(spec, "credentials.kubeconfig.context")
            )
        except ValueError as exc:
            raise kopf.TemporaryError(
                f"Failed to extract kubeconfig context from secret {secret_ref_name} required for cluster configuration {name}.",  # pylint: disable=line-too-long
                delay=5 if not retry else 15,
            ) from exc

    else:
        server = "https://kubernetes.default.svc"

        kubeconfig = create_kubeconfig_from_access_token_secret(
            "/opt/cluster-access-token", name, server
        )

    # Update the cluster configuration in the cluster database.

    logger.info(
        "%s cluster configuration %r with generation %s.",
        (reason == "update") and "Update" or "Register",
        name,
        generation,
    )

    cluster_database = memo.cluster_database

    cluster_database.update_cluster(
        ClusterConfiguration(
            name=name,
            uid=uid,
            labels=xgetattr(spec, "labels", {}),
            kubeconfig=kubeconfig,
        ),
    )


@kopf.on.delete("clusterconfigs.lookup.educates.dev")
def clusterconfigs_delete(name: str, memo: ServiceState, **_):
    """Remove the cluster configuration from the cluster database."""

    generation = memo.get("generation")

    cluster_database = memo.cluster_database

    logger.info("Delete cluster configuration %r with generation %s", name, generation)

    cluster_database.remove_cluster(name)


class ClusterOperator(GenericOperator):
    """Operator for interacting with training platform on separate cluster."""

    def __init__(self, cluster_name: str, service_state: ServiceState) -> None:
        """Initializes the operator."""

        super().__init__(cluster_name, service_state=service_state)

    def register_handlers(self) -> None:
        """Register the handlers for the training platform operator."""

        @kopf.on.event(
            "trainingportals.training.educates.dev",
            registry=self.operator_registry,
        )
        def trainingportals_event(event: kopf.RawEvent, memo: ServiceState, **_):
            """Handles events for training portals."""

            portal_database = memo.portal_database

            body = xgetattr(event, "object", {})
            metadata = xgetattr(body, "metadata", {})
            spec = xgetattr(body, "spec", {})
            status = xgetattr(body, "status", {})

            portal_name = xgetattr(metadata, "name")

            if xgetattr(event, "type") == "DELETED":
                logger.info(
                    "Discard training portal %s of cluster %s",
                    portal_name,
                    self.cluster_name,
                )

                portal_database.remove_portal(self.cluster_name, portal_name)

            else:
                logger.info(
                    "Register training portal %s of cluster %s",
                    portal_name,
                    self.cluster_name,
                )

                auth = PortalAuth(
                    client_id=xgetattr(status, "educates.clients.robot.id"),
                    client_secret=xgetattr(status, "educates.clients.robot.secret"),
                    username=xgetattr(status, "educates.credentials.robot.username"),
                    password=xgetattr(status, "educates.credentials.robot.password"),
                )

                portal = PortalState(
                    name=portal_name,
                    uid=xgetattr(metadata, "uid"),
                    generation=xgetattr(metadata, "generation"),
                    labels=xgetattr(spec, "portal.labels", {}),
                    cluster=self.cluster_name,
                    url=xgetattr(status, "educates.url"),
                    phase=xgetattr(status, "educates.phase"),
                    auth=auth,
                )

                portal_database.update_portal(portal)

        @kopf.on.event(
            "workshopenvironments.training.educates.dev",
            labels={"training.educates.dev/portal.name": kopf.PRESENT},
            registry=self.operator_registry,
        )
        def workshopenvironments_event(event: kopf.RawEvent, memo: ServiceState, **_):
            """Handles events for workshop environments."""

            workshop_database = memo.workshop_database

            body = xgetattr(event, "object", {})
            metadata = xgetattr(body, "metadata", {})
            spec = xgetattr(body, "spec", {})
            status = xgetattr(body, "status", {})

            portal_name = xgetattr(metadata, "labels", {}).get(
                "training.educates.dev/portal.name"
            )
            environment_name = xgetattr(metadata, "name")
            workshop_name = xgetattr(spec, "workshop.name")

            workshop_generation = xgetattr(status, "educates.workshop.generation", 0)
            workshop_spec = xgetattr(status, "educates.workshop.spec", {})

            if xgetattr(event, "type") == "DELETED":
                logger.info(
                    "Discard workshop environment %s from portal %s of cluster %s",
                    workshop_name,
                    portal_name,
                    self.cluster_name,
                )

                workshop_database.remove_workshop(
                    self.cluster_name, portal_name, environment_name
                )

            else:
                logger.info(
                    "Register workshop environment %s from portal %s of cluster %s",
                    workshop_name,
                    portal_name,
                    self.cluster_name,
                )

                workshop_details = WorkshopDetails(
                    name=workshop_name,
                    generation=workshop_generation,
                    title=xgetattr(workshop_spec, "title"),
                    description=xgetattr(workshop_spec, "description"),
                    labels=xgetattr(workshop_spec, "labels", {}),
                    cluster=self.cluster_name,
                    portal=portal_name,
                    environment=environment_name,
                    phase=xgetattr(status, "educates.phase"),
                )

                workshop_database.update_workshop(workshop_details)


@kopf.daemon(
    "clusterconfigs.lookup.educates.dev",
    cancellation_backoff=5.0,
    cancellation_polling=5.0,
)
def clusterconfigs_daemon(
    stopped: kopf.DaemonStopped,
    name: str,
    uid: str,
    retry: int,
    memo: ServiceState,
    **_,
) -> None:
    """Starts an instance of the cluster operator for each registere cluster and
    waits for it to complete."""

    # Make sure we have separately processed the cluster config resource so
    # that an item exists for it in the cache and it has the same uid.

    cache = memo.cluster_database

    cluster = cache.get_cluster_by_name(name)

    if not cluster or cluster.uid != uid:
        raise kopf.TemporaryError(
            f"Cluster {name} with uid {uid} not found.",
            delay=5 if not retry else 15,
        )

    # Start the cluster operator and wait for it to complete. An infinite loop
    # is used to keep the daemon thread running until the daemon is stopped as
    # kopf framework expects this daemon thread to be running indefinitely until
    # it is stopped.

    operator = ClusterOperator(name, memo)

    operator.run_until_stopped(stopped)
