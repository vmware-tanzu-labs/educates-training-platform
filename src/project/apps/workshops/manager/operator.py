"""Defines initialization functions for starting up kopf operator framework
in a separate thread.

"""

import asyncio
import contextlib
import functools
import logging

from threading import Thread, Event

from asgiref.sync import sync_to_async

import mod_wsgi
import kopf


_event_loop = None  # pylint: disable=invalid-name


def event_loop():
    return _event_loop


class Task:
    def __init__(self, wrapped, name, delay, repeat, args, kwargs):
        self.wrapped = wrapped
        self.name = name
        self.delay = delay
        self.repeat = repeat
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        return self.wrapped(*self.args, **self.kwargs)

    def schedule(self, *, delay=None):
        delay = delay or self.delay

        async def sleep():
            if delay > 0.0:
                await asyncio.sleep(self.delay)

        @sync_to_async
        def execute():
            try:
                logging.info("Executing task %s %s %s.", self.name, self.args, self.kwargs)
                return self.wrapped(*self.args, **self.kwargs)
            except Exception:  # pylint: disable=broad-except
                logging.exception("Exception raised by task %s.", self.name)

        async def task():
            await sleep()

            if self.repeat:
                while True:
                    await execute()
                    await sleep()

            else:
                return await execute()

        return asyncio.run_coroutine_threadsafe(task(), _event_loop)


def background_task(wrapped=None, *, name=None, delay=0.0, repeat=False):
    """Designates a synchronous function as an asynchronous task. The function
    can be defined to be executed once, or set up to be called repeatedly.

    """

    if wrapped is None:
        return functools.partial(background_task, delay=delay, repeat=repeat)

    name = name or wrapped.__qualname__

    def wrapper(*args, **kwargs):
        return Task(wrapped, name, delay, repeat, args, kwargs)

    return wrapper


def initialize_kopf():
    """Run kopf in a separate thread and register shutdown handler with
    mod_wsgi to ensure we clean things up properly on process shutdown.

    """

    ready_flag = Event()
    stop_flag = Event()

    def worker():
        logging.info("Starting kopf framework main loop.")

        # Need to create and set the event loop since this isn't being
        # called in the main thread.

        global _event_loop  # pylint: disable=invalid-name,global-statement

        _event_loop = asyncio.new_event_loop()

        asyncio.set_event_loop(_event_loop)

        with contextlib.closing(_event_loop):
            # Turn on verbose logs from kopf framework.

            # kopf.configure(log_format="%(levelname)s:%(name)s - %(message)s")

            # Run event loop until flagged to shutdown.

            _event_loop.run_until_complete(
                kopf.operator(ready_flag=ready_flag, stop_flag=stop_flag)
            )

        logging.info("Exiting kopf framework main loop.")

    thread = Thread(target=worker)

    def shutdown_handler(*_, **__):
        stop_flag.set()
        thread.join()

    mod_wsgi.subscribe_shutdown(shutdown_handler)  # pylint: disable=no-member

    # Startup kopf framework.

    thread.start()

    # Wait until kopf has initialized before continuing.

    ready_flag.wait()
