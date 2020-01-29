Workshop Definition
===================

The ``Workshop`` custom resource defines a workshop.

The raw custom resource definition for the ``Workshop`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/workshop.yaml

Workshop title and description
------------------------------

Each workshop is required to provide the ``vendor``, ``title``, ``description`` and ``url`` fields. If the fields are not supplied, the ``Workshop`` resource will be rejected when you attempt to load it into the Kubernetes cluster.

.. code-block:: yaml
    :emphasize-lines: 6-9

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

The ``vendor`` field should be a value which uniquely identifies who is providing the workshop. It is recommended this should be a DNS hostname under the control of whoever has created the workshop.

The ``title`` field should be a single line value giving the subject of the workshop.

The ``description`` field should be a longer description of the workshop. This can be multi line if necessary.

The ``url`` field should be a URL you can go to for more information about the workshop.

The following optional information can also be supplied for the workshop.

.. code-block:: yaml
    :emphasize-lines: 11

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

The ``duration`` field gives the expected maximum amount of time the workshop would take to complete. This field only provides informational value and is not used to police how long a workshop instance will last. The format of the field is an integer number with ``s``, ``m``, or ``h`` suffix.

Note that when referring to a workshop definition after it has been loaded into a Kubernetes cluster, the value of ``name`` field given in the metadata is used. If you want to play around with slightly different variations of a workshop, copy the original workshop definition YAML file and change the value of ``name``. Then make your changes and load it into the Kubernetes cluster.

Container image for the workshop
--------------------------------

An ``image`` field is required and needs to specify the image reference identifying the location of the container image to be deployed for the workshop instance. If the field is not supplied, the ``Workshop`` resource will be rejected when you attempt to load it into the Kubernetes cluster.

.. code-block:: yaml
    :emphasize-lines: 10

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

There are two options for what the ``image`` field may refer to.

The first option is that it can be a custom container image which builds on top of the eduk8s project ``workshop-dashboard`` image. This custom image would include the content for the workshop, as well as any additional tools or files used for the workshop. The container image therefore acts as the distribution mechanism for the workshop. The container image must be hosted by an image registry accessible to the Kubernetes cluster.

The second option is that the eduk8s project ``workshop-dashboard`` image is used, with the workshop content being pulled down to the workshop instance when it starts from a GitHub project repository or web server. The location of such remote content needs to be specified via an environment variable.

Setting environment variables
-----------------------------

If you want to set or override environment variables for the workshop instance, you can supply the ``session.env`` field.

.. code-block:: yaml
    :emphasize-lines: 11-14

    apiVersion: training.eduk8s.io/v1alpha1
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      vendor: eduk8s.io
      title: Markdown Sample
      description: A sample workshop using Markdown
      url: https://github.com/eduk8s/lab-markdown-sample
      image: quay.io/eduk8s/workshop-dashboard:master
      session:
        env:
        - name: DOWNLOAD_URL
          value: github.com/eduk8s/lab-markdown-sample

The ``session.env`` field should be a list of dictionaries with ``name`` and ``value`` fields.

Note that the ability to override environment variables using this field should be limited to cases where they are required for the workshop. If you want to set or override an environment for a specific workshop environment, use the ability to set environment variables in the ``WorkshopEnvironment`` custom resource for the workshop environment instead.

Resource budget for namespaces
------------------------------

...

Patching workshop deployment
----------------------------

...

Creation of session resources
-----------------------------

...

Overriding default RBAC rules
-----------------------------

...

Creating additional namespaces
------------------------------

...

Shared workshop resources
-------------------------

...

Using remote workshop content
-----------------------------

...
