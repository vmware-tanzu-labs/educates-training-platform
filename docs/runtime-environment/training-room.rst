Training Room
=============

The ``TrainingRoom`` custom resource triggers the deployment of a workshop environment and a set number of workshop instances.

The raw custom resource definition for the ``TrainingRoom`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/training-room.yaml

Specifying the workshop definition
----------------------------------

Running multiple workshop instances to perform training to a group of people can be done by following the step wise process of creating the workshop environment, and then creating each workshop instance. The ``TrainingRoom`` workshop resource bundles that up as one step.

Before creating the training environment you still need to load the workshop definition as a separate step.

To specify which workshop definition is to be used for the training, set the ``workshop.name`` field of the specification for the training environment.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingRoom
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample

The ``name`` of the training environment specified in the ``metadata`` of the training environment does not need to be the same, and has to be different if creating multiple training environments from the same workshop definition.

When the training environment is created, it will setup the underlying workshop environment, create the required number of workshop instances, and deploy a web portal for attendees of the training to access their workshop instance.

Capacity of the training room
-----------------------------

If you do not say how many workshop instances should be created, the training room will be setup with a single workshop instance. If you want to declare the number of workshop instances to create, set the ``session.capacity`` field.

.. code-block:: yaml
    :emphasize-lines: 8-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingRoom
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        capacity: 8

When setting the number of workshop instances to create in this way, the session IDs will be named with ``user`` prefix, followed by the number of the session, starting at 1.

The list of workshop instances created can be queried by running:

.. code-block:: text

    kubectl get workshopsessions

This will show output like:

.. code-block:: text

    NAME                        URL                                    USERNAME   PASSWORD
    lab-markdown-sample-user1   http://lab-markdownsample-user1.test   eduk8s     W3Jt4fiUAOIH2zrF

Overriding the login credentials
--------------------------------

Access to each workshop instance is controlled through login credentials. This is so that a workshop attendee cannot interfere with another. By default the login name for a workshop instance is ``eduk8s``. The password for each workshop instance will be randomly generated.

If you want to override the login name, or set a common password which is the same for all workshop instances, you can set the ``session.username`` and ``session.password`` fields.

.. code-block:: yaml
    :emphasize-lines: 9-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingRoom
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        username: eduk8s
        password: lab-markdown-sample

Overriding the ingress domain
-----------------------------

The URL for accessing workshop instances, and the web portal for the training environment, will use the ingress domain configured into the eduk8s operator. If you need to override this for the training environment, you can set the ``session.domain`` field.

.. code-block:: yaml
    :emphasize-lines: 9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingRoom
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        domain: training.eduk8s.io

Setting extra environment variables
-----------------------------------

If you want to override any environment variables for all workshop instances, you can provide the environment variables in the ``session.env`` field.

.. code-block:: yaml
    :emphasize-lines: 9-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingRoom
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        env:
        - name: REGISTRY_HOST
          value: registry.eduk8s.io

Customizing details of sessions
-------------------------------

If you want more control over the details of each workshop instance, including being able to control the session ID, username, password, and environment variables set for the workshop instance, you can provide your own list with details by setting ``session.attendees``.

.. code-block:: yaml
    :emphasize-lines: 9-15

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingRoom
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      session:
        attendees:
        - id: user1
          username: eduk8s
          password: lab-markdown-sample
          env:
          - name: REGISTRY_HOST
            value: registry.eduk8s.io

When you specify a list of attendees, the ``session.capacity`` field will be ignored. The number of workshop instances will instead be determined by the number of sessions described in ``session.attendees``.

If ``username`` and ``password`` fields for an attendee are not set, the defaults for the training environment, or overrides, will instead be used.

Any environment variables set for the session of an attendee will be added in addition to any extra environment variables set for the training environment.
