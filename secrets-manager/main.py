import asyncio
import contextlib
import logging
import signal

from threading import Thread, Event

import kopf

from handlers import namespace
from handlers import secret
from handlers import secretcopier
from handlers import secretexporter
from handlers import secretimporter
from handlers import secretinjector
from handlers import serviceaccount

_event_loop = None  # pylint: disable=invalid-name

logger = logging.getLogger("educates.operator")


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.DEBUG


_stop_flag = Event()


def run_kopf():
    """Run kopf in a separate thread and wait for it to complete."""

    def worker():
        logger.info("Starting kopf framework main loop.")

        # Need to create and set the event loop since this isn't being
        # called in the main thread.

        global _event_loop  # pylint: disable=invalid-name,global-statement

        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)

        with contextlib.closing(_event_loop):
            # Run event loop until flagged to shutdown.

            _event_loop.run_until_complete(
                kopf.operator(clusterwide=True, stop_flag=_stop_flag)
            )

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
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    thread = run_kopf()
    thread.join()
