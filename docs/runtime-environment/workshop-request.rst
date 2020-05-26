Workshop Request
================

The ``WorkshopRequest`` custom resource defines a workshop request.

The raw custom resource definition for the ``WorkshopRequest`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/workshop-request.yaml

Specifying workshop environment
-------------------------------

The ``WorkshopRequest`` custom resource is only used to request a workshop instance. It does not specify actual details needed to perform the deployment of the workshop instance. That information is instead sourced by the eduk8s operator from the ``WorkshopEnvironment`` and ``Workshop`` custom resources.

The minimum required information in the workshop request is therefore just the name of the workshop environment. This is supplied by setting the ``environment.name`` field.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopRequest
    metadata:
      name: lab-markdown-sample
    spec:
      environment:
        name: lab-markdown-sample

If multiple workshop requests, whether for the same workshop environment or different ones, are created in the same namespace, the ``name`` defined in the ``metadata`` for the workshop request must be different for each. The value of this name is not important and is not used in naming of workshop instances. A user will need to remember it if they want to delete the workshop instance, which is done by deleting the workshop request.

Specifying required access token
--------------------------------

Where a workshop environment has been configured to require an access token when making workshop request against that environment, it can be specified by setting the ``environment.token`` field.

.. code-block:: yaml
    :emphasize-lines: 8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: WorkshopRequest
    metadata:
      name: lab-markdown-sample
    spec:
      environment:
        name: lab-markdown-sample
        token: lab-markdown-sample

Even with the token, if the workshop environment has restricted the namespaces a workshop request has been made from, and the workshop request was not created in one of the white listed namespaces, the request will fail.
