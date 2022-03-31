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


class Task:
    """Encapsulation of an instance of a background task. It binds the
    function implementing the task with the arguments to use when calling it,
    along with details of when to call it and whether it should run as a
    periodic task.

    """

    def __init__(
        self, wrapped, name, delay, repeat, args, kwargs
    ):  # pylint: disable=too-many-arguments
        """Capture details of the function implementing the task and the
        parameters for invoking it.

        """

        self.wrapped = wrapped
        self.name = name
        self.delay = delay
        self.repeat = repeat
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        """Execute the function for the task synchronously."""

        return self.wrapped(*self.args, **self.kwargs)

    def schedule(self, *, delay=None):
        """Schedule a task to be run using the asyncio library. The delay
        before running the task which was originally specified can be
        overridden at this point if necessary.

        """

        delay = delay or self.delay

        async def sleep():
            if delay > 0.0:
                await asyncio.sleep(delay)

        @sync_to_async(thread_sensitive=False)
        def execute():
            """Executes the function, capturing details of any exception and
            logging it since nothing will even wait on the results.

            """

            try:
                logging.info(
                    "Executing task %s %s %s.", self.name, self.args, self.kwargs
                )
                return self.wrapped(*self.args, **self.kwargs)

            except Exception:  # pylint: disable=broad-except
                logging.exception("Exception raised by task %s.", self.name)

        async def task():
            """The asynchronous task wrapper for the function. Handles once
            off execution as well as looping forever with delay.

            """

            await sleep()

            if self.repeat:
                while True:
                    await execute()
                    await sleep()

            else:
                return await execute()

        # This schedules the task to be run by the asyncio loop. This is
        # done using threadsafe registration mechanism as can be called by
        # request handler thread of mod_wsgi and not necessarily a function
        # executing under asyncio.

        return asyncio.run_coroutine_threadsafe(task(), _event_loop)


def background_task(wrapped=None, *, name=None, delay=0.0, repeat=False):
    """Designates a synchronous function as an asynchronous task. The function
    can be defined to be executed once, or set up to be called repeatedly.

    """

    # Parameters for the task are optional so if any were supplied return
    # a partially bound version of the decorator function for subsequent
    # applyication to the function implementing the task.

    if wrapped is None:
        return functools.partial(background_task, delay=delay, repeat=repeat)

    name = name or wrapped.__qualname__

    # Return a function which encapsulates the details of the task and which
    # in turn returns a task wrapper object. Code using this still needs to
    # called either execute() or schedule() on the task object which is
    # returned.

    def wrapper(*args, **kwargs):
        return Task(wrapped, name, delay, repeat, args, kwargs)

    return wrapper


def initialize_kopf():
    """Run kopf in a separate thread and register a shutdown handler with
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
            # Run event loop until flagged to shutdown.

            _event_loop.run_until_complete(
                kopf.operator(
                    clusterwide=True, ready_flag=ready_flag, stop_flag=stop_flag
                )
            )

        logging.info("Exiting kopf framework main loop.")

    thread = Thread(target=worker)

    # Register the shutdown handler with mod_wsgi so everything cleaned
    # up properly when the process is being stopped.

    def shutdown_handler(*_, **__):
        stop_flag.set()
        thread.join()

    mod_wsgi.subscribe_shutdown(shutdown_handler)  # pylint: disable=no-member

    # Startup kopf framework.

    thread.start()

    # Wait until kopf has initialized before continuing.

    ready_flag.wait()
