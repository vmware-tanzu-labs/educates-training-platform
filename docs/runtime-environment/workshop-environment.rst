Workshop Environment
====================

The ``WorkshopEnvironment`` custom resource defines a workshop environment.

The raw custom resource definition for the ``WorkshopEnvironment`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/environment.yaml

Specifying the workshop definition
----------------------------------

The creation of a workshop environment is performed as a separate step to loading the workshop definition. This is to allow multiple distinct workshop environments using the same workshop definition to be created if necessary.

To specify which workshop definition is to be used for a workshop environment, set the ``workshop.name`` field of the specification for the workshop environment.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample

The ``name`` of the workshop environment specified in the ``metadata`` of the workshop environment does not need to be the same, and has to be different if creating multiple workshop environments from the same workshop definition.

When the workshop environment is created, the namespace created for the workshop environment will use the ``name`` of the workshop environment specified in the ``metadata``. This name will also be used in the unique names of each workshop instance created under the workshop environment.

Overriding environment variables
--------------------------------

A workshop definition may specify a list of environment variables that need to be set for all workshop instances. If you need to override an environment variable specified in the workshop definition, or one which is defined in the container image, you can supply a list of environment variables as ``session.env``.

.. code-block:: yaml
    :emphasize-lines: 8-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        env:
        - name: REGISTRY_HOST
          value: registry.eduk8s.io

You might use this to set the location of a backend service, such as an image registry, to be used by the workshop.

Overriding the ingress domain
-----------------------------

When requesting a workshop using ``WorkshopRequest``, an ingress route will be created to allow the workshop instance to be created. By default the domain used in the host name of the URL, will be determined by the value of the ``INGRESS_DOMAIN`` environment variable set on the eduk8s operator deployment. If you need to override this domain to use an alternate custom domain, you can set ``session.domain``.

.. code-block:: yaml
    :emphasize-lines: 8-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        domain: training.eduk8s.io

When setting a custom domain, DNS must have been configured with a wildcard domain to forward all requests for sub domains of the custom domain, to the ingress router of the Kubernetes cluster.

Controlling access to the workshop
----------------------------------

By default, anyone able to create a ``WorkshopRequest`` custom resource, will be able to request a workshop instance in the workshop environment.

To control who can request a workshop instance in the workshop environment, you can first set an access token, which a user would need to know and supply with the workshop request. This can be done by setting the ``request.token`` field.

.. code-block:: yaml
    :emphasize-lines: 8-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      request:
        token: lab-markdown-sample

In this example the same name as the workshop environment is used, which is probably not a good practice. Use a random value instead. The token value can be multiline if desired.

As a second measure of control, you can specify what namespaces the ``WorkshopRequest`` needs to be created in to be successful. This means a user would need to have the specific ability to create ``WorkshopRequest`` resources in one of those namespaces.

The list of namespaces from which workshop requests for the workshop environment is allowed can be specified by setting ``request.namespaces``.

.. code-block:: yaml
    :emphasize-lines: 10-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      request:
        token: lab-markdown-sample
        namespaces:
        - default

If you want to add the workshop namespace in the list, rather than list the literal name, you can reference a predefined parameter specifying the workshop namespace by including ``$(workshop_namespace)``.

.. code-block:: yaml
    :emphasize-lines: 10-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      request:
        token: lab-markdown-sample
        namespaces:
        - $(workshop_namespace)

Overriding the login credentials
--------------------------------

When requesting a workshop using ``WorkshopRequest``, a login prompt for the workshop instance will be presented to a user when the URL for the workshop instance is accessed. By default the username they need to use will be ``eduk8s``. The password will be a random value which they need to query from the ``WorkshopRequest`` status after the custom resource has been created.

If you want to override the username, you can specify the ``session.username`` field. If you want to set the same fixed password for all workshop instances, you can specify the ``session.password`` field.

.. code-block:: yaml
    :emphasize-lines: 8-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        username: workshop
        password: lab-markdown-sample
