import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

import asyncio
import contextlib
import logging
import signal

from threading import Thread, Event

import kopf
import pykube

from handlers import workshopenvironment
from handlers import workshopsession
from handlers import workshopallocation
from handlers import trainingportal

from handlers import daemons

_event_loop = None  # pylint: disable=invalid-name

logger = logging.getLogger("educates")
logger.setLevel(logging.DEBUG)

_stop_flag = Event()


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.DEBUG
    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 5 * 60
    settings.watching.client_timeout = settings.watching.server_timeout + 10


@kopf.on.login()
def login_fn(**kwargs):
    return kopf.login_via_pykube(**kwargs)


@kopf.on.probe(id='api')
def check_api_access(**kwargs):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        pykube.Namespace.objects(api).get(name="default")

    except pykube.exceptions.KubernetesError:
        logger.error("Failed request to Kubernetes API.")

        raise


@kopf.on.cleanup()
async def cleanup_fn(logger, **kwargs):
    logger.info("Stopping kopf framework main loop.")

    # Workaround for possible kopf bug, set stop flag.

    _stop_flag.set()


def run_kopf():
    """Run kopf in a separate thread and wait for it to complete."""

    def worker():
        logger.info("Starting kopf framework main loop.")

        # Need to create and set the event loop since this isn't being
        # called in the main thread.

        global _event_loop  # pylint: disable=invalid-name,global-statement

        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)

        # Schedule background task to purge namespaces.

        _event_loop.create_task(daemons.purge_namespaces())

        with contextlib.closing(_event_loop):
            # Run event loop until flagged to shutdown.

            _event_loop.run_until_complete(
                kopf.operator(
                    clusterwide=True,
                    stop_flag=_stop_flag,
                    liveness_endpoint="http://0.0.0.0:8080/healthz",
                )
            )

            logger.info("Closing asyncio event loop.")

        logger.info("Exiting kopf framework main loop.")

    thread = Thread(target=worker)

    # Startup kopf framework.

    thread.start()

    return thread


def shutdown(signum, frame):
    logger.info("Signal handler called with signal %s.", signum)
    if _event_loop:
        _stop_flag.set()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    thread = run_kopf()
    thread.join()
