Custom Resources
================

It is possible to deploy workshop images directly to a container runtime, but for managing deployments into a Kubernetes cluster, the eduk8s operator is provided. The operation of the eduk8s operator is controlled through a set of Kubernetes custom resource definitions (CRDs).

Not all possible fields are shown in the examples of each custom resource type below. Later documentation will go into depth on all the possible fields that can be set and what they do.

Workshop definition resource
----------------------------

The ``Workshop`` custom resource defines a workshop. It specifies the title and description of the workshop, the container image to be deployed, any resources to be pre-created in the workshop environment, or for each instance of the workshop. You can also define environment variables to be set for the workshop image when deployed, the amount of CPU and memory resources for the workshop instance, and any overall quota to be applied to namespaces created for the user and which would be used by the workshop.

A minimal example of the ``Workshop`` custom resource is:

.. code-block:: yaml

    apiVersion: training.eduk8s.io/v1alpha1
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      vendor: eduk8s.io
      title: Markdown Sample
      description: A sample workshop using Markdown
      url: https://github.com/eduk8s/lab-markdown-sample
      image: quay.io/eduk8s/lab-markdown-sample:master
      duration: 15m
      session:
        budget: small

The raw custom resource definition for the ``Workshop`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/request.yaml

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

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/environment.yaml

The ``WorkshopEnvironment`` custom resource is created at cluster scope.

Workshop request resource
-------------------------

Workshop session resource
-------------------------

Loading the workshop CRDs
-------------------------
