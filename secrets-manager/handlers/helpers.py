import threading


class global_logger:

    local = threading.local()

    def __init__(self, logger):
        self.logger = logger

    def __enter__(self):
        self.previous = getattr(global_logger.local, "current", None)
        global_logger.local.current = self.logger

    def __exit__(self, *args):
        global_logger.local.current = self.previous


def get_logger():
    return global_logger.local.current


def lookup(obj, key, default=None):
    """Looks up a property within an object using a dotted path as key.
    If the property isn't found, then return the default value.

    """

    keys = key.split(".")
    value = default

    for key in keys:
        value = obj.get(key)
        if value is None:
            return default

        obj = value

    return value
