"""Main entry point for the lookup service. This module starts the kopf
operator framework and the aiohttp server for handling REST API requests."""

import asyncio
import contextlib
import logging
import signal
import threading

import kopf
import pykube
import aiohttp

from .service import ServiceState

from .caches.clients import ClientDatabase
from .caches.clusters import ClusterDatabase
from .caches.tenants import TenantDatabase

from .routes.authnz import jwt_token_middleware, api_login_handler

from .routes.clients import api_v1_clients, api_v1_clients_details

from .routes.tenants import api_v1_tenants, api_v1_tenants_details

from .routes.clusters import (
    api_v1_clusters,
    api_v1_clusters_details,
    api_v1_clusters_kubeconfig,
)

from .routes.workshops import api_post_v1_workshops

# We need to import the modules for operator handlers so that they are
# registered with the operator framework.

from .handlers import clients as _  # pylint: disable=unused-import
from .handlers import tenants as _  # pylint: disable=unused-import
from .handlers import clusters as _  # pylint: disable=unused-import

# Set up logging for the educates operator.

logging.getLogger("kopf.activities.probe").setLevel(logging.WARNING)
logging.getLogger("kopf.objects").setLevel(logging.WARNING)

logger = logging.getLogger("educates")

# Register the operator handlers for the training platform operator.
#
# TODO: These handler registrations are done against the global kopf registry
# and thus will not apply to secondary operator instances which are created in
# separate threads later as they will use their own registry. This means
# liveness probes aren't currently checking access to secondary clusters. Also
# need to check whether settings are being applied to the secondary operator
# instances.


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_) -> None:
    """Configures the kopf operator settings."""

    settings.posting.level = logging.ERROR
    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 5 * 60
    settings.watching.client_timeout = settings.watching.server_timeout + 10


@kopf.on.login()
def login_fn(**kwargs) -> dict:
    """Returns login credentials to be used by the kopf operator framework using
    the pykube library so that the operator framework is using the same means of
    getting credentials as the pykube library."""

    return kopf.login_via_pykube(**kwargs)


@kopf.on.probe(id="api")
def check_api_access(**_) -> None:
    """Checks if we can access the Kubernetes API for the liveness probe. The
    kopf framework will handle the response to the liveness probe based on
    the result of this function. The kopf operator framework will also do
    basic checks to determine if the operator is still running and if it is
    able to process events."""

    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        pykube.Namespace.objects(api).get(name="default")

    except pykube.exceptions.KubernetesError:
        logger.error("Failed liveness probe request to Kubernetes API.")

        raise


# Process variables and shutdown handling. Signal handlers run in the main
# thread so we need to use global event objects to signal the kopf framework
# and HTTP server, which run in separate threads, to stop processing.

_kopf_main_process_thread = None  # pylint: disable=invalid-name
_kopf_main_event_loop = None  # pylint: disable=invalid-name

_aiohttp_main_process_thread = None  # pylint: disable=invalid-name
_aiohttp_main_event_loop = None  # pylint: disable=invalid-name

_shutdown_server_process_flag = threading.Event()


def shutdown_server_process(signum: int, *_) -> None:
    """Signal handler for shutting down the server process. This will set the
    stop flag for the kopf framework and HTTP server to stop processing."""

    logger.info("Signal handler called with signal %s.", signum)

    if _kopf_main_event_loop:
        _shutdown_server_process_flag.set()


def register_signal_handlers() -> None:
    """Registers signal handlers for the server process. This will allow the
    server process to be shutdown cleanly when a signal is received."""

    signal.signal(signal.SIGINT, shutdown_server_process)
    signal.signal(signal.SIGTERM, shutdown_server_process)


@kopf.on.cleanup()
async def cleanup_fn(**_) -> None:
    """Cleanup function for the operator."""

    # TODO: This is a workaround for a possible bug in kopf where the cleanup
    # function isn't being called when the operator is stopped. This sets the
    # stop flag for the operator to stop processing again. This may no longer
    # be required.

    _shutdown_server_process_flag.set()


# Global data structures to be shared across the kopf operator and uvicorn
# server threads.

client_database = ClientDatabase()
tenant_database = TenantDatabase()
cluster_database = ClusterDatabase()

service_state = ServiceState(
    client_database=client_database,
    tenant_database=tenant_database,
    cluster_database=cluster_database,
)


def run_kopf() -> threading.Thread:
    """Run kopf in a separate thread."""

    def worker_thread():
        logger.info("Starting kopf framework main loop.")

        # Need to create and set the event loop since this isn't being
        # called in the main thread.

        global _kopf_main_event_loop  # pylint: disable=global-statement

        _kopf_main_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_kopf_main_event_loop)

        # Run the kopf operator framework until the shutdown flag is set.

        # TODO: This currently only checks the educates-platform namespace.
        # This should be updated to allow namespace to be specified via an
        # environment variable passed into Kubernetes pod and passed via a
        # command line argument to the operator.

        with contextlib.closing(_kopf_main_event_loop):
            _kopf_main_event_loop.run_until_complete(
                kopf.operator(
                    clusterwide=False,
                    namespaces=["educates-platform"],
                    stop_flag=_shutdown_server_process_flag,
                    memo=service_state,
                    liveness_endpoint="http://0.0.0.0:8081/healthz",
                )
            )

    # Start the kopf operator framework in a separate thread.

    thread = threading.Thread(target=worker_thread)
    thread.start()

    return thread


def run_aiohttp() -> threading.Thread:
    """Run aiohttp in a separate thread."""

    aiohttp_app = aiohttp.web.Application()

    aiohttp_app["service_state"] = service_state

    aiohttp_app.router.add_post("/login", api_login_handler)

    aiohttp_app.router.add_get("/api/v1/clients", api_v1_clients)
    aiohttp_app.router.add_get("/api/v1/clients/{name}", api_v1_clients_details)

    aiohttp_app.router.add_get("/api/v1/tenants", api_v1_tenants)
    aiohttp_app.router.add_get("/api/v1/tenants/{name}", api_v1_tenants_details)

    aiohttp_app.router.add_get("/api/v1/clusters", api_v1_clusters)
    aiohttp_app.router.add_get("/api/v1/clusters/{name}", api_v1_clusters_details)
    aiohttp_app.router.add_get(
        "/api/v1/clusters/{name}/kubeconfig", api_v1_clusters_kubeconfig
    )

    aiohttp_app.router.add_post("/api/v1/workshops", api_post_v1_workshops)

    aiohttp_app.middlewares.append(jwt_token_middleware)

    runner = aiohttp.web.AppRunner(aiohttp_app)

    async def wait_for_process_shutdown() -> None:
        """Wait for the server process to shutdown and then shutdown the HTTP
        server."""

        # Wait for the shutdown flag to be set.

        while not _shutdown_server_process_flag.is_set():
            await asyncio.sleep(1)

        # Shutdown the aiohttp server.

        await runner.cleanup()

    def worker_thread() -> None:
        """Worker thread for running the HTTP server."""

        # Need to create a separate event loop for the HTTP server since this
        # isn't being called in the main thread.

        global _aiohttp_main_event_loop  # pylint: disable=global-statement

        _aiohttp_main_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_aiohttp_main_event_loop)

        async def run_app() -> None:
            await runner.setup()
            site = aiohttp.web.TCPSite(runner, "0.0.0.0", 8080)
            await site.start()

        with contextlib.closing(_aiohttp_main_event_loop):
            _aiohttp_main_event_loop.run_until_complete(
                asyncio.gather(run_app(), wait_for_process_shutdown())
            )

    # Start the HTTP server in a separate thread.

    thread = threading.Thread(target=worker_thread)
    thread.start()

    return thread


# Main entry point for the educates operator. This will start the kopf operator
# framework and the HTTP server.

if __name__ == "__main__":

    # Set up logging for the educates operator.

    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)

    # Suppress verbose logging from urllib3 if ever set general log level to
    # more verbose setting.

    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    # Register signal handlers for the server process.

    register_signal_handlers()

    # Start the kopf framework and HTTP server threads.

    _kopf_main_process_thread = run_kopf()
    _aiohttp_main_process_thread = run_aiohttp()

    # Wait for the kopf framework and HTTP server threads to complete. This
    # will block until the threads are finished which will only occur when the
    # shutdown process signal is received.

    _kopf_main_process_thread.join()
    _aiohttp_main_process_thread.join()
