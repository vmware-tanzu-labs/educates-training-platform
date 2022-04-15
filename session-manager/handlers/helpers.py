def xget(obj, key, default=None):
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


class Applications:
    defaults = {
        "console": False,
        "docker": False,
        "editor": False,
        "files": False,
        "examiner": False,
        "registry": False,
        "slides": True,
        "terminal": True,
        "webdav": False,
    }

    def __init__(self, configuration):
        self.configuration = configuration

    def names(self):
        return self.defaults.keys()

    def is_enabled(self, name):
        return self.configuration.get(name, {}).get(
            "enabled", self.defaults.get(name, False)
        )

    def properties(self, name):
        return self.configuration.setdefault(name, {})

    def property(self, name, key, default=None):
        properties = self.properties(name)
        keys = key.split(".")
        value = default
        for key in keys:
            value = properties.get(key)
            if value is None:
                return default
            properties = value
        return value