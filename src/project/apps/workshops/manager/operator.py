"""Defines initialization functions for starting up kopf operator framework
in a separate thread.

"""

import asyncio
import contextlib

from threading import Thread, Event

import mod_wsgi
import kopf


_event_loop = None  # pylint: disable=invalid-name


def event_loop():
    return _event_loop


def call_periodically(interval):
    """Creates an asyncio task which runs the wrapped function periodically
    with interval defined in seconds.

    """

    def wrapper1(wrapped):
        def wrapper2(*args, **kwargs):
            async def task():
                while True:
                    await asyncio.sleep(interval)
                    await wrapped(*args, **kwargs)

            return task()

        return wrapper2

    return wrapper1


def schedule_task(coro):
    return asyncio.run_coroutine_threadsafe(coro, _event_loop)


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

        global _event_loop  # pylint: disable=invalid-name,global-statement

        _event_loop = asyncio.new_event_loop()

        asyncio.set_event_loop(_event_loop)

        with contextlib.closing(_event_loop):
            # Turn on verbose logs from kopf framework.

            kopf.configure(verbose=True)

            # Run event loop until flagged to shutdown.

            _event_loop.run_until_complete(
                kopf.operator(ready_flag=ready_flag, stop_flag=stop_flag)
            )

        print("Exiting kopf framework main loop.")

    thread = Thread(target=worker)

    def shutdown_handler(*_, **__):
        stop_flag.set()
        thread.join()

    mod_wsgi.subscribe_shutdown(shutdown_handler)  # pylint: disable=no-member

    # Startup kopf framework.

    thread.start()

    # Wait until kopf has initialized before continuing.

    ready_flag.wait()
