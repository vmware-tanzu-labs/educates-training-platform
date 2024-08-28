"""Helper functions for accessing objects."""

from typing import Any


def xgetattr(obj: Any, key: str, default: Any = None) -> Any:
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
