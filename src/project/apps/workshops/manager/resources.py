"""Defines wrapper objects to make it slightly easier to work with Kubernetes
resource objects.

"""


class ResourceListView:
    """Implements base wrapper for a list structure forming part of a
    Kubernetes resource object.

    """

    def __init__(self, obj):
        self.__obj = obj

    def __str__(self):
        return str(self.__obj)

    def __len__(self):
        return len(self.__obj)

    def __getitem__(self, index):
        value = self.__obj[index]

        if isinstance(value, dict):
            return ResourceDictView(value)

        if isinstance(value, (list, tuple)):
            return ResourceListView(value)

        return value

    def __iter__(self):
        for value in self.__obj:
            if isinstance(value, dict):
                yield ResourceDictView(value)
            elif isinstance(value, (list, tuple)):
                yield ResourceListView(value)
            else:
                yield value

    def obj(self):
        return self.__obj


class ResourceDictView:
    """Implements base wrapper for a dictionary structure forming part of a
    Kubernetes resource object.

    """

    def __init__(self, obj):
        self.__obj = obj

    def __str__(self):
        return str(self.__obj)

    def __len__(self):
        return len(self.__obj)

    def __getitem__(self, key):
        value = self.__obj[key]

        if isinstance(value, dict):
            return ResourceDictView(value)

        if isinstance(value, (list, tuple)):
            return ResourceListView(value)

        return value

    def __iter__(self):
        for value in self.__obj:
            if isinstance(value, dict):
                yield ResourceDictView(value)
            elif isinstance(value, (list, tuple)):
                yield ResourceListView(value)
            else:
                yield value

    def keys(self):
        return self.__obj.keys()

    def values(self):
        return self.__obj.values()

    def items(self):
        return self.__obj.items()

    def get(self, key, default=None):
        obj = self.__obj

        keys = key.split(".")
        value = default

        for key in keys:
            value = obj.get(key)
            if value is None:
                if isinstance(default, dict):
                    return ResourceDictView(default)

                if isinstance(default, (list, tuple)):
                    return ResourceListView(default)

                return default

            obj = value

        if isinstance(value, dict):
            return ResourceDictView(value)

        if isinstance(value, (list, tuple)):
            return ResourceListView(value)

        return value

    def obj(self):
        return self.__obj


class ResourceMetadata(ResourceDictView):
    """Implements wrapper around metadata section of a Kubernetes resource
    object.

    """

    @property
    def name(self):
        return self.get("name")

    @property
    def namespace(self):
        return self.get("namespace")

    @property
    def labels(self):
        return self.get("labels", {})

    @property
    def annotations(self):
        return self.get("annotation", {})


class ResourceBody(ResourceDictView):
    """Implements wrapper around the complete body of a Kubernetes resource
    object.

    """

    @property
    def metadata(self):
        return ResourceMetadata(self.get("metadata", {}))

    @property
    def spec(self):
        return self.get("spec", {})

    @property
    def status(self):
        return self.get("status", {})
