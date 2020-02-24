Training Portal
===============

The ``TrainingPortal`` custom resource triggers the deployment of a set of workshop environments and a set number of workshop instances.

The raw custom resource definition for the ``TrainingPortal`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/training-portal.yaml

Specifying the workshop definition
----------------------------------

Running multiple workshop instances to perform training to a group of people can be done by following the step wise process of creating the workshop environment, and then creating each workshop instance. The ``TrainingPortal`` workshop resource bundles that up as one step.

Before creating the training environment you still need to load the workshop definition as a separate step.

To specify the names of the workshops to be used for the training, list them under the ``workshops`` field of training portal specification. Each entry needs to define a ``name`` property, matching the name of the ``Workshop`` resource which was created.

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

When setting up the training portal you need to say how many workshop instances should be created for each workshop. To do this set the ``portal.capacity`` field.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 8
      workshops:
      - name: lab-markdown-sample

When setting the number of workshop instances to create in this way, the session IDs will be named with ``user`` prefix, followed by the number of the session, starting at 1.

The list of workshop instances created can be queried by running:

.. code-block:: text

    kubectl get workshopsessions

This will show output like:

.. code-block:: text

    NAME                        URL                                    USERNAME   PASSWORD
    lab-markdown-sample-user1   http://lab-markdownsample-user1.test   eduk8s     W3Jt4fiUAOIH2zrF

Overriding the ingress domain
-----------------------------

The URL for accessing workshop instances, and the web portal for the training environment, will use the ingress domain configured into the eduk8s operator. If you need to override this for the training environment, you can set the ``portal.domain`` field.

.. code-block:: yaml
    :emphasize-lines: 8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 1
        domain: training.eduk8s.io
      workshops:
      - name: lab-markdown-sample

Setting extra environment variables
-----------------------------------

If you want to override any environment variables for workshop instances created for a specific work, you can provide the environment variables in the ``env`` field of that workshop.

.. code-block:: yaml
    :emphasize-lines: 10-12

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 1
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

The syntax for referencing one of the parameters is ``$(parameter_name)``.
