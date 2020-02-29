Workshop Session
================

The ``WorkshopSession`` custom resource defines a workshop session.

The raw custom resource definition for the ``WorkshopSession`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/workshop-session.yaml

Specifying the session identity
-------------------------------

When running training for multiple people, it would be more typical to use the ``TrainingPortal`` custom resource to set up a training environment. Alternatively you would set up a workshop environment using the ``WorkshopEnvironment`` custom resource, then create requests for workshop instances using the ``WorkshopRequest`` custom resource. If doing the latter and you need more control over how the workshop instances are set up, you can use ``WorkshopSession`` custom resource instead of ``WorkshopRequest``.

To specify the workshop environment the workshop instance is created against, set the ``environment.name`` field of the specification for the workshop session. At the same time, you must specify the session ID for the workshop instance.

.. code-block:: yaml
    :emphasize-lines: 6-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopSession
    metadata:
      name: lab-markdown-sample-user1
    spec:
      environment:
        name: lab-markdown-sample
      session:
        id: user1

The ``name`` of the workshop specified in the ``metadata`` of the training environment needs to be globally unique for the workshop instance being created. You would need to create a separate ``WorkshopSession`` custom resource for each workshop instance you want.

The session ID needs to be unique within the workshop environment the workshop instance is being created against.

Specifying the login credentials
--------------------------------

Access to each workshop instance can be controlled through login credentials. This is so that a workshop attendee cannot interfere with another.

If you want to set login credentials for a workshop instance, you can set the ``session.username`` and ``session.password`` fields.

.. code-block:: yaml
    :emphasize-lines: 9-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopSession
    metadata:
      name: lab-markdown-sample
    spec:
      environment:
        name: lab-markdown-sample-user1
      session:
        username: eduk8s
        password: lab-markdown-sample

If you do not specify login credentials, there will not be any access controls on the workshop instance and anyone will be able to access it.

Specifying the ingress domain
-----------------------------

In order to be able to access the workshop instance using a public URL, you will need to specify an ingress domain. If an ingress domain isn't specified, a default of ``training.eduk8s.io`` will be used.

To provide the ingress domain, you can set the ``session.domain`` field.

.. code-block:: yaml
    :emphasize-lines: 9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopSession
    metadata:
      name: lab-markdown-sample
    spec:
      environment:
        name: lab-markdown-sample-user1
      session:
        domain: training.eduk8s.io

When you specify just the ingress domain, a full hostname will be created by prefixing the ingress domain with a hostname constructed from the name of the workshop environment and the session ID.

Setting the environment variables
---------------------------------

If you want to set the environment variables for the workshop instance, you can provide the environment variables in the ``session.env`` field.

.. code-block:: yaml
    :emphasize-lines: 9-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopSession
    metadata:
      name: lab-markdown-sample
    spec:
      environment:
        name: lab-markdown-sample
      session:
        id: user1
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

Note that if the workshop environment had specified a set of extra environment variables to be set for workshop instances, it is up to you to incorporate those in the set of environment variables you list under ``session.env``. That is, anything listed in ``session.env`` of the ``WorkshopEnvironment`` custom resource of the workshop environment is ignored.
