import asyncio
import contextlib
import logging

from threading import Thread

import kopf

from handlers import *
from daemons import *

_event_loop = None  # pylint: disable=invalid-name


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.DEBUG


def run_kopf():
    """Run kopf in a separate thread and wait for it to complete.

    """

    def worker():
        logger.info("Starting kopf framework main loop.")

        # Need to create and set the event loop since this isn't being
        # called in the main thread.

        global _event_loop  # pylint: disable=invalid-name,global-statement

        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)

        # Schedule background task to purge namespaces.

        _event_loop.create_task(purge_namespaces())

        with contextlib.closing(_event_loop):
            # Run event loop until flagged to shutdown.

            _event_loop.run_until_complete(kopf.operator(clusterwide=True))

        logger.info("Exiting kopf framework main loop.")

    thread = Thread(target=worker)

    # Startup kopf framework.

    thread.start()

    return thread


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    thread = run_kopf()
    thread.join()
