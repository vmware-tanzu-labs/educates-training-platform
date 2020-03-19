Training Portal
===============

The ``TrainingPortal`` custom resource triggers the deployment of a set of workshop environments and a set number of workshop instances.

The raw custom resource definition for the ``TrainingPortal`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/training-portal.yaml

Specifying the workshop definition
----------------------------------

Running multiple workshop instances to perform training to a group of people can be done by following the step wise process of creating the workshop environment, and then creating each workshop instance. The ``TrainingPortal`` workshop resource bundles that up as one step.

Before creating the training environment you still need to load the workshop definition as a separate step.

To specify the names of the workshops to be used for the training, list them under the ``workshops`` field of the training portal specification. Each entry needs to define a ``name`` property, matching the name of the ``Workshop`` resource which was created.

.. code-block:: yaml
    :emphasize-lines: 8-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 1
      workshops:
      - name: lab-markdown-sample

The ``name`` of the training portal specified in the ``metadata`` of the training portal does not need to be the same, and logically would need to be different if creating a training portal for multiple workshops.

When the training portal is created, it will setup the underlying workshop environments, create the required number of workshop instances for each workshop, and deploy a web portal for attendees of the training to access their workshop instances.

Capacity of the training portal
-------------------------------

When setting up the training portal you need to specify a maximum for the number of workshop instances that can be created for each workshop. To do this set the ``portal.capacity`` field.

.. code-block:: yaml
    :emphasize-lines: 6-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 8
        reserved: 1
      workshops:
      - name: lab-markdown-sample

This is a maximum capacity only. How many workshop sessions will be pre-created in advance will depend on whether ``portal.reserved`` is also defined.

If ``portal.reserved`` is not defined, then as many workshop sessions as is defined by ``portal.capacity`` will be created up front.

If ``portal.reserved`` is defined, then only as many workshop sessions as it specifies will be created up front. Except where the maximum capacity would be exceeded, each time one of the reserved workshop instances is allocated to a user, a new workshop session will also be created to ensure that the required number of reserved instances are always ready.

Where you have multiple workshops listed, if you don't want them all to have the same capacity and number of reserved instances, you can specify theses settings against each workshop instead.

.. code-block:: yaml
    :emphasize-lines: 6-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 8
        reserved: 1

Expiring of workshop sessions
-----------------------------

Once you reach the maximum capacity, no more workshops sessions can be created. Once a workshop session has been allocated to a user, they cannot be re-assigned to another user.

If running a supervised workshop you therefore need to ensure that you set the capacity higher than the expected number in case you have extra users you didn't expect which you need to accomodate. You can use the setting for the reserved number of instances so that although a higher capacity is set, workshop sessions are only created as required, rather than all being created up front.

For supervised workshops when the training is over you would delete the whole training environment and all workshop sessions would then be deleted.

If you need to host a training portal over an extended period and you don't know when users will want to do a workshop, you can setup workshop sessions to expire after a set time. When expired the workshop session will be deleted, and a new workshop session can be created in its place.

The maximum capacity is therefore the maximum at any one point in time, with the number being able to grow and shrink over time. In this way, over an extended time you could handle many more sessions that what the maximum capacity is set to. The maximum capacity is in this case used to ensure you don't try and allocate more workshop sessions than you have resources to handle at any one time.

Setting a maximum time allowed for a workshop session can be done using the ``portal.expires`` setting.

.. code-block:: yaml
    :emphasize-lines: 9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 8
        reserved: 1
        expires: 60m
      workshops:
      - name: lab-markdown-sample

The ``expires`` setting can also be set against a specific workshop as well.

The value needs to be an integer, followed by a suffix of 's', 'm' or 'h', corresponding to seconds, minutes or hours.

The time period is calculated from when the workshop session is allocated to a user. When the time period is up, the workshop session will be automatically deleted.

When an expiration period is specified, when a user finishes a workshop, or restarts the workshop, it will also be deleted.

To cope with users who grab a workshop session, but then leave and don't actually use it, you can also set a time period for when a workshop session with no activity is deemed as being orphaned and so deleted.

.. code-block:: yaml
    :emphasize-lines: 10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 8
        reserved: 1
        expires: 60m
        orphaned: 5m
      workshops:
      - name: lab-markdown-sample

For supervised workshops, you should avoid this setting so that a users session is not deleted when they take breaks and their computer sleeps.

Overriding the ingress domain
-----------------------------

The URL for accessing workshop instances, and the web portal for the training environment, will use the ingress domain configured into the eduk8s operator. If you need to override this for the training environment, you can set the ``portal.domain`` field.

.. code-block:: yaml
    :emphasize-lines: 9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 3
        reserved: 1
        domain: training.eduk8s.io
      workshops:
      - name: lab-markdown-sample

Setting extra environment variables
-----------------------------------

If you want to override any environment variables for workshop instances created for a specific work, you can provide the environment variables in the ``env`` field of that workshop.

.. code-block:: yaml
    :emphasize-lines: 11-13

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 3
        reserved: 1
      workshops:
      - name: lab-markdown-sample
        env:
        - name: REGISTRY_HOST
          value: registry.eduk8s.io

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``service_account`` - The name of the service account the workshop instance runs as, and which has access to the namespace created for that workshop instance.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The syntax for referencing one of the parameters is ``$(parameter_name)``.
