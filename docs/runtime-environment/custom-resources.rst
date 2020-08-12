Custom Resources
================

It is possible to deploy workshop images directly to a container runtime, but for managing deployments into a Kubernetes cluster, the eduk8s operator is provided. The operation of the eduk8s operator is controlled through a set of Kubernetes custom resource definitions (CRDs).

Not all possible fields are shown in the examples of each custom resource type below. Later documentation will go into depth on all the possible fields that can be set and what they do.

Workshop definition resource
----------------------------

The ``Workshop`` custom resource defines a workshop. It specifies the title and description of the workshop, the location of the workshop content or container image to be deployed, any resources to be pre-created in the workshop environment, or for each instance of the workshop. You can also define environment variables to be set for the workshop image when deployed, the amount of CPU and memory resources for the workshop instance, and any overall quota to be applied to namespaces created for the user and which would be used by the workshop.

A minimal example of the ``Workshop`` custom resource is:

.. code-block:: yaml

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
        files: github.com/eduk8s/lab-markdown-sample
      session:
        namespaces:
          budget: small
        applications:
          console:
            enabled: true
          editor:
            enabled: true

The raw custom resource definition for the ``Workshop`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/workshop.yaml

When an instance of the ``Workshop`` custom resource is created it does not cause any immediate action by the eduk8s operator. This custom resource exists only to define the workshop.

The ``Workshop`` custom resource is created at cluster scope.

Workshop environment resource
-----------------------------

In order to deploy instances of a workshop, you first need to create a workshop environment. The configuration for the workshop environment, and which workshop definition specifies the details of the workshop to be deployed, is defined the by the ``WorkshopEnvironment`` custom resource.

A minimal example of the ``WorkshopEnvironment`` custom resource is:

.. code-block:: yaml

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopEnvironment
    metadata:
      name: lab-markdown-sample
    spec:
      workshop:
        name: lab-markdown-sample
      request:
        token: lab-markdown-sample
      session:
        username: eduk8s

When an instance of the ``WorkshopEnvironment`` custom resource is created, the eduk8s operator responds by creating a namespace for hosting the workshop instances defined by the ``Workshop`` resource specified by the ``spec.workshop.name`` field. The namespace created will use the same name as specified by the ``metadata.name`` field of the ``WorkshopEnvironment`` resource.

The ``spec.request.token`` field defines a token which must be supplied with a request to create an instance of a workshop in this workshop environment. If necessary, the namespaces from which a request for a workshop instance can be initiated can also be specified.

If the ``Workshop`` definition for the workshop to be deployed in this workshop environment defines a set of common resources which must exist for the workshop, these will be created by the eduk8s operator after the namespace for the workshop environment is created. Where such resources are namespaced, they will be created in the namespace for the workshop environment. If necessary, these resources can include creation of separate namespaces with specific resources created in those namespaces instead.

The raw custom resource definition for the ``WorkshopEnvironment`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/workshop-environment.yaml

The ``WorkshopEnvironment`` custom resource is created at cluster scope.

Workshop request resource
-------------------------

To create an instance of the workshop under the workshop environment which was created, the typical path is to create an instance of the ``WorkshopRequest`` custom resource.

The ``WorkshopRequest`` custom resource is namespaced to allow who can create it and so request a workshop instance to be created, to be controlled through RBAC. This means it is possible to allow non privileged users to create workshops, even though the deployment of the workshop instance may need elevated privileges.

A minimal example of the ``WorkshopRequest`` custom resource is:

.. code-block:: yaml

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopRequest
    metadata:
      name: lab-markdown-sample
    spec:
      environment:
        name: lab-markdown-sample
        token: lab-markdown-sample

Apart from needing to have appropriate access through RBAC, the only information that the user requesting a workshop instance needs to know is the the name of the workshop environment for the workshop, and the secret token which permits workshop requests against that specific workshop environment.

The raw custom resource definition for the ``WorkshopRequest`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/workshop-request.yaml

Workshop session resource
-------------------------

Although ``WorkshopRequest`` would be the typical way that workshop instances would be requested, upon the request being granted, the eduk8s operator will itself create an instance of a ``WorkshopSession`` custom resource.

The ``WorkshopSession`` custom resource is the expanded definition of what the workshop instance should look like. It combines details from ``Workshop`` and ``WorkshopEnvironment``, and also links back to the ``WorkshopRequest`` resource object which triggered the request. The eduk8s operator reacts to an instance of ``WorkshopSession`` and creates the workshop instance based on that definition.

The raw custom resource definition for the ``WorkshopSession`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/workshop-session.yaml

The ``WorkshopSession`` custom resource is created at cluster scope.

Training portal resource
------------------------

The ``TrainingPortal`` custom resource provides a high level mechanism for creating a set of workshop environments and populating them with workshop instances.

A minimal example of the ``TrainingPortal`` custom resource is:

.. code-block:: yaml

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 1

You can set the capacity of the training room and that dictates how many workshop instances are created for each workshop.

The raw custom resource definition for the ``TrainingPortal`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/training-room.yaml

The ``TrainingPortal`` custom resource is created at cluster scope.

System profile resource
-----------------------

The ``SystemProfile`` custom resources provides a mechanism for configuring the eduk8s operator. This provides additional features above using using environment variables to configure the operator.

A minimal example of the ``SystemProfile`` custom resource is:

.. code-block:: yaml

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      ingress:
        domain: training.eduk8s.io
        secret: training-eduks8-io-tls
        class: nginx
      environment:
        secrets:
          pull:
          - cluster-image-registry-pull

The operator by default will look for a default system profile called ``default-system-profile``. The name of the default can be overridden globally by setting the ``SYSTEM_PROFILE`` environment variable on the deployment for the operator, or for specific deployments via the ``system.profile`` setting on ``TrainingPortal``, ``WorkshopEnvironment`` or ``WorkshopSession`` custom resources.

As only a global deployment of the operator is supported, the ``SystemProfile`` custom resource is created at cluster scope.

Changes can be made to instances of the ``SystemProfile`` custom resource and they will be automatically used by the eduk8s operator without needing to redeploy it.

The raw custom resource definition for the ``SystemProfile`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/system-profile.yaml

The ``SystemProfile`` custom resource is created at cluster scope.

Loading the workshop CRDs
-------------------------

The custom resource definitions for the custom resource described above, are created in the Kubernetes cluster when you deploy the eduk8s operator using the command:

.. code-block:: text

    kubectl apply -k "github.com/eduk8s/eduk8s?ref=master"

Although links to the ``v1`` versions of the CRDs are given above, at this time this command will actually use the ``v1beta1`` versions of the CRDs. This is because ``v1`` versions of CRDs are only supported from Kubernetes 1.17. If for some reason you need to use the ``v1`` versions of the CRDs at this time, you will need to create a copy of the eduk8s operator deployment resources and override the configuration so that the ``v1`` versions are used.

The location of the ``v1beta1`` versions of the CRDs is:

* https://github.com/eduk8s/eduk8s/tree/develop/resources/crds-v1beta1

and those for ``v1`` versions is:

* https://github.com/eduk8s/eduk8s/tree/develop/resources/crds-v1
