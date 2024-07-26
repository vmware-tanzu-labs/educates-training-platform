"""Base class and helper functions for kopf based operator."""

import asyncio
import contextlib
import threading
import time
import logging

import kopf
import aiohttp


from ..service import ServiceState
from .kubeconfig import create_connection_info_from_kubeconfig

logger = logging.getLogger("educates")


class GenericOperator(threading.Thread):
    """Base class for kopf based operator."""

    def __init__(
        self, cluster_name: str, *, namespaces: str = None, service_state: ServiceState
    ) -> None:
        """Initializes the operator."""

        super().__init__()

        # Set the name of the operator and the namespaces to watch for
        # resources. When the list of namespaces is empty, the operator will
        # watch for resources cluster wide.

        self.cluster_name = cluster_name
        self.namespaces = namespaces or []

        # Set the state object for the operator. This is used to store the state
        # of the operator across invocations.

        self.service_state = service_state

        # Create an operator registry to store the handlers for the operator.
        # We need a distinct registry for each operator since we need to be able
        # to run multiple operators in the same process with separate handlers.

        self.operator_registry = kopf.OperatorRegistry()

        # Create a stop flag to signal the operator to stop running. This is
        # used to bridge between the kopf variable for stopping the operator
        # and event required to stop the event loop for the operator.

        self._stop_flag = threading.Event()

    def register_handlers(self) -> None:
        """Register the handlers for the operator."""

        raise NotImplementedError("Subclasses must implement this method.")

    def run(self) -> None:
        """Starts the kopf operator in a separate event loop."""

        # Register the login function for the operator.

        @kopf.on.login(registry=self.operator_registry)
        def login_fn(**_) -> dict:
            """Returns login credentials for the cluster calculated from the
            configuration currently held in the cluster configuration cache."""

            # TODO: Not dealing with fact that configuration may have been
            # deleted from the cache between when we checked for it and now.

            cache = self.service_state.cluster_database

            cluster = cache.get_cluster_by_name(self.cluster_name)

            return create_connection_info_from_kubeconfig(cluster.kubeconfig)

        @kopf.on.cleanup()
        async def cleanup_fn(**_) -> None:
            """Cleanup function for operator."""

            # Workaround for possible kopf bug, set stop flag.

            self._stop_flag.set()

        # Register the kopf handlers for this operator.

        self.register_handlers()

        # Determine if the operator should be run clusterwide or in specific
        # namespaces.

        clusterwide = False

        if not self.namespaces:
            clusterwide = True

        # Run the operator in a separate event loop, waiting for the stop flag
        # to be set, at which point the operator will be stopped and this thread
        # will exit.

        while not self._stop_flag.is_set():
            event_loop = asyncio.new_event_loop()

            asyncio.set_event_loop(event_loop)

            logger.info("Starting managed cluster operator for %s.", self.cluster_name)

            with contextlib.closing(event_loop):
                try:
                    event_loop.run_until_complete(
                        kopf.operator(
                            registry=self.operator_registry,
                            clusterwide=clusterwide,
                            namespaces=self.namespaces,
                            memo=self.service_state,
                            stop_flag=self._stop_flag,
                        )
                    )

                except (
                    aiohttp.client_exceptions.ClientConnectorError,
                    aiohttp.client_exceptions.ClientConnectorCertificateError,
                ):
                    # If the operator exits due to a connection error it means it
                    # could not connect to the cluster on initial startup. After
                    # a short delay, the operator will be restarted.

                    logger.exception(
                        "Connection error, restarting operator after delay."
                    )

                    time.sleep(5.0)

    def cancel(self) -> None:
        """Flags the kopf operatot to stop."""

        # Set the stop flag to stop the operator. This will cause the event loop
        # to stop running and the operator thread to exit.

        self._stop_flag.set()

    def run_until_stopped(self, stopped: kopf.DaemonStopped) -> None:
        """Run the operator until stopped."""

        self.start()

        while not stopped:
            # We should be called from a traditional thread so it is safe to use
            # blocking sleep call.

            time.sleep(1.0)

        self.cancel()

        self.join()
