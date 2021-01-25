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
        """Returns the value from the list at the specified index position.
        When the value is a dictionary it is returned wrapped up in an
        instance of ResourceDictView. When the value is a list or tuple is is
        returned wrapped up in an instance of ResourceListView.

        """

        value = self.__obj[index]

        if isinstance(value, dict):
            return ResourceDictView(value)

        if isinstance(value, (list, tuple)):
            return ResourceListView(value)

        return value

    def __iter__(self):
        """Returns an iterator over the values from the view. When the value
        is a dictionary it is returned wrapped up in an instance of
        ResourceDictView. When the value is a list or tuple is is returned
        wrapped up in an instance of ResourceListView.

        """

        for value in self.__obj:
            if isinstance(value, dict):
                yield ResourceDictView(value)
            elif isinstance(value, (list, tuple)):
                yield ResourceListView(value)
            else:
                yield value

    def obj(self):
        """Returns the raw Python object representation."""

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
        """Returns the value from the dictionary indexed by the specified key.
        When the value is a dictionary it is returned wrapped up in an
        instance of ResourceDictView. When the value is a list or tuple is is
        returned wrapped up in an instance of ResourceListView.

        """

        value = self.__obj[key]

        if isinstance(value, dict):
            return ResourceDictView(value)

        if isinstance(value, (list, tuple)):
            return ResourceListView(value)

        return value

    def __iter__(self):
        """Returns an iterator over the values from the view. When the value
        is a dictionary it is returned wrapped up in an instance of
        ResourceDictView. When the value is a list or tuple is is returned
        wrapped up in an instance of ResourceListView.

        """

        for value in self.__obj:
            if isinstance(value, dict):
                yield ResourceDictView(value)
            elif isinstance(value, (list, tuple)):
                yield ResourceListView(value)
            else:
                yield value

    def keys(self):
        """Returns the keys from the dictionary."""

        return self.__obj.keys()

    def values(self):
        """Returns the values from the dictionary."""

        return self.__obj.values()

    def items(self):
        """Returns the key/value pairs from the dictionary as tuples."""

        return self.__obj.items()

    def get(self, key, default=None):
        """Returns a target value based on a dotted path supplied via the
        key. When the value is a dictionary it is returned wrapped up in
        an instance of ResourceDictView. When the value is a list or tuple
        is is returned wrapped up in an instance of ResourceListView.

        """

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
        """Returns the raw Python object representation."""

        return self.__obj


class ResourceMetadata(ResourceDictView):
    """Implements wrapper around metadata section of a Kubernetes resource
    object.

    """

    @property
    def name(self):
        """Returns the name of the Kubernetes resource object."""

        return self.get("name")

    @property
    def uid(self):
        """Returns the uid of the Kubernetes resource object."""

        return self.get("uid")

    @property
    def generation(self):
        """Returns the generation of the Kubernetes resource object."""

        return self.get("generation")

    @property
    def namespace(self):
        """If present, returns the namespace in which the Kubernetes resource
        object exists.

        """

        return self.get("namespace")

    @property
    def labels(self):
        """If present, returns any labels associated with the Kubernetes
        resource object.

        """

        return self.get("labels", {})

    @property
    def annotations(self):
        """If present, returns any annotations associated with the Kubernetes
        resource object.

        """

        return self.get("annotation", {})


class ResourceBody(ResourceDictView):
    """Implements wrapper around the complete body of a Kubernetes resource
    object.

    """

    @property
    def name(self):
        """Returns the name of the Kubernetes resource object."""

        return self.get("metadata.name")

    @property
    def metadata(self):
        """Returns a view over the metadata section of the Kubernetes resource
        object.

        """

        return ResourceMetadata(self.get("metadata", {}))

    @property
    def spec(self):
        """Returns a view over the spec section of the Kubernetes resource
        object.

        """

        return self.get("spec", {})

    @property
    def status(self):
        """Returns a view over the status section of the Kubernetes resource
        object.

        """

        return self.get("status", {})
