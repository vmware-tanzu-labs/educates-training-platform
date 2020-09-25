"""Defines initialization functions for starting up kopf operator framework
in a separate thread.

"""

import asyncio
import contextlib

from threading import Thread, Event

import mod_wsgi
import kopf


def initialize_kopf():
    """Run kopf in a separate thread and register shutdown handler with
    mod_wsgi to ensure we clean things up properly on process shutdown.

    """

    ready_flag = Event()
    stop_flag = Event()

    def worker():
        print("Starting kopf framework main loop.")

        # Need to create and set the event loop since this isn't being
        # called in the main thread.

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with contextlib.closing(loop):
            # Turn on verbose logs from kopf framework.

            kopf.configure(verbose=True)

            # Run event loop until flagged to shutdown.

            loop.run_until_complete(
                kopf.operator(ready_flag=ready_flag, stop_flag=stop_flag)
            )

        print("Exiting kopf framework main loop.")

    thread = Thread(target=worker)

    def shutdown_handler(*_, **__):
        stop_flag.set()
        thread.join()

    mod_wsgi.subscribe_shutdown(shutdown_handler)

    # Startup kopf framework.

    thread.start()

    # Wait until kopf has initialized before continuing.

    ready_flag.wait()
