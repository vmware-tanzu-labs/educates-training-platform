"""Implementation of a global lock for database operations affecting workshop
sessions.

"""

import threading

import wrapt


_global_lock = threading.Lock()


def resources_lock(wrapped=None):
    """Returns a lock when used for context manager, or decorator when
    applied to a function.

    """

    if wrapped is None:
        return _global_lock

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):  # pylint: disable=unused-argument
        with _global_lock:
            return wrapped(*args, **kwargs)

    return wrapper(wrapped)  # pylint: disable=no-value-for-parameter
