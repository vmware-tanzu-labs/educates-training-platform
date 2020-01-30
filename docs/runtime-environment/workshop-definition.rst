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

In conjunction with each workshop instance, a namespace will be created for use during the workshop. That is, from the terminal of the workshop dashboard applications can be deployed into the namespace via the Kubernetes REST API using tools such as ``kubectl``.

By default this namespace will have whatever limit ranges and resource quota which may be enforced by the Kubernetes cluster. In most case this will mean there are no limits or quotas. The exception is likely OpenShift, which through a project template can automatically apply limit ranges and quotas to new namespaces when created.

To control how much resources can be used where no limit ranges and resource quotas are set, or to override any default limit ranges and resource quota, you can set a resource budget for any namespaces created for the workshop instance.

To set the resource budget, set the ``session.budget`` field.

.. code-block:: yaml
    :emphasize-lines: 11-12

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
      session:
        budget: small

The resource budget sizings are:

* ``small`` - 1Gi memory
* ``medium`` - 2Gi memory
* ``large`` - 4Gi memory
* ``x-large`` - 8Gi memory
* ``xx-large`` - 12Gi memory
* ``xxx-large`` - 16Gi memory

Only the memory quota is given above, but many more parameters are fixed by what budget you specify. These include object counts, limit ranges for CPU and memory on a container and pod basis, and quotas on CPU and memory. Separate resource quotas are applied for terminating and non terminating workloads.

For more precise details of what constraints will be applied for a specific resource budget size, consult the code definitions for each in the eduk8s operator code file for session creation.

* https://github.com/eduk8s/eduk8s-operator/blob/develop/operator/session.py

If you need to run a workshop with different limit ranges and resource quotas, you should set the resource budget to ``custom``. This will remove any default limit ranges and resource quota which might be applied to the namespace. You can then specify your own ``LimitRange`` and ``ResourceQuota`` resources as part of the list of resources created for each session.

Patching workshop deployment
----------------------------

In order to set or override environment variables you can provide ``session.env``. If you need to make other changes to the pod template for the deployment used to create the workshop instance, you need to provide an overlay patch. Such a patch might be used to override the default CPU and memory limit applied to the workshop instance, or to mount a volume.

The patches are provided by setting ``session.patches``. The patch will be applied to the ``spec`` field of the pod template.

.. code-block:: yaml
    :emphasize-lines: 11-19

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
      session:
        patches:
          containers:
          - name: workshop
            resources:
              requests:
                memory: "1Gi"
              limits:
                memory: "1Gi"

In this example the default memory limit of "512Mi" is increased to "1Gi".

The patch when applied works a bit differently to overlay patches as found elsewhere in Kubernetes. Specifically, when patching an array and the array contains a list of objects, a search is performed on the destination array and if an object already exists with the same value for the ``name`` field, the item in the source array will be overlaid on top of the existing item in the destination array. If there is no matching item in the destination array, the item in the source array will be added to the end of the destination array.

This means an array doesn't outright replace an existing array, but a more intelligent merge is performed of elements in the array.

Creation of session resources
-----------------------------

When a workshop instance is created, the deployment running the workshop dashboard is created in the namespace for the workshop environment. When more than one workshop instance is created under that workshop environment, all those deployments are in the same namespace.

For each workshop instance, a separate empty namespace is created with name corresponding to the workshop session. The workshop instance is configured so that the service account that the workshop instance runs under, can access and create resources in the namespace created for that workshop instance. Each separate workshop instance has its own corresponding namespace and they can't see the namespace for another instance.

If you want to pre-create additional resources within the namespace for a workshop instance, you can supply a list of the resources as ``session.objects`` within the workshop definition. You might use this to add additional custom roles to the service account for the workshop instance when working in that namespace, or to deploy a distinct instance of an application for just that workshop instance, such as a private image registry.

.. code-block:: yaml
    :emphasize-lines: 11-49

    apiVersion: training.eduk8s.io/v1alpha1
    kind: Workshop
    metadata:
      name: lab-admin-testing
    spec:
      vendor: eduk8s.io
      title: Admin Testing
      description: Play area for testing cluster admin
      url: https://github.com/eduk8s-tests/lab-admin-testing
      image: quay.io/eduk8s-tests/lab-admin-testing:master
      session:
        objects:
        - apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: registry
          spec:
            replicas: 1
            selector:
              matchLabels:
                deployment: registry
            strategy:
              type: Recreate
            template:
              metadata:
                labels:
                  deployment: registry
              spec:
                containers:
                - name: registry
                  image: registry.hub.docker.com/library/registry:2.6.1
                  imagePullPolicy: IfNotPresent
                  ports:
                  - containerPort: 5000
                    protocol: TCP
                  env:
                  - name: REGISTRY_STORAGE_DELETE_ENABLED
                    value: "true"
        - apiVersion: v1
          kind: Service
          metadata:
            name: registry
          spec:
            type: ClusterIP
            ports:
            - port: 80
              targetPort: 5000
            selector:
              deployment: registry

Note that for namespaced resources, it is not necessary to specify the ``namespace`` field of the resource ``metadata``. When the ``namespace`` field is not present the resource will automatically be created within the session namespace for that workshop instance.

When resources are created, owner references are added making the ``WorkshopSession`` custom resource corresponding to the workshop instance the owner. This means that when the workshop instance is deleted, any cluster scoped resources will be automatically deleted.

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``service_account`` - The name of the service account the workshop instance runs as, and which has access to the namespace created for that workshop instance.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.

The syntax for reference one of the parameters is ``$(parameter_name)``.

In the case of cluster scoped resources, it is important that you set the name of the created resource so that it embeds the value of ``$(session_namespace)``. This way the resource name is unique to the workshop instance and you will not get a clash with a resource for a different workshop instance.

.. code-block:: yaml
    :emphasize-lines: 11-24

    apiVersion: training.eduk8s.io/v1alpha1
    kind: Workshop
    metadata:
      name: lab-admin-testing
    spec:
      vendor: eduk8s.io
      title: Admin Testing
      description: Play area for testing cluster admin
      url: https://github.com/eduk8s-tests/lab-admin-testing
      image: quay.io/eduk8s-tests/lab-admin-testing:master
      session:
        objects:
        - apiVersion: rbac.authorization.k8s.io/v1
          kind: ClusterRoleBinding
          metadata:
            name: $(session_namespace)-cluster-admin
          roleRef:
            apiGroup: rbac.authorization.k8s.io
            kind: ClusterRole
            name: cluster-admin
          subjects:
          - kind: ServiceAccount
            namespace: $(workshop_namespace)
            name: $(service_account)

Overriding default RBAC rules
-----------------------------

...

Creating additional namespaces
------------------------------

...

Shared workshop resources
-------------------------

...

Downloading workshop content
----------------------------

Bundling workshop content into an image built off the eduk8s ``workshop-dashboard`` image means the container image becomes the distribution mechanism for the workshop, including any additional tools and files it needs.

The alternative is to use the eduk8s ``workshop-dashboard`` image and download any workshop content at the time the workshop instance is created. Provided the amount of content is not too great, this shouldn't affect startup times for the workshop instance.

To download workshop content at the time the workshop instance is started, set the ``image`` field to ``quay.io/eduk8s/workshop-dashboard:master`` and then add a ``session.env`` section and set the ``DOWNLOAD_URL`` environment variable to the location of the workshop content.

.. code-block:: yaml
    :emphasize-lines: 10-14

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

The ``DOWNLOAD_URL`` environment variable can be either a GitHub repository reference, or a URL to a tarball hosted on a HTTP server.

In the case of a GitHub repository, do not prefix the location with ``https://`` as this is a symbolic reference and not an actual URL.

The format of the reference to the GitHub repository is similar to that used with kustomize when referencing GitHub repositories. For example:

* ``github.com/organisation/project`` - Use the workshop content hosted at the root of the Git repository. The ``master`` branch is used.
* ``github.com/organisation/project/subdir?ref=develop`` - Use the workshop content hosted at ``subdir`` of the Git repository. The ``develop`` branch is used.

In the case of a URL to a tarball hosted on a HTTP server, the workshop content is taken from the top level directory of the unpacked tarball. It is not possible to specify a subdirectory within the tarball. This means you cannot use a URL reference to refer to release tarballs which are automatically created by GitHub, as these place content in a subdirectory corresponding to the release name, branch or Git reference. For GitHub repositories, always use the GitHub repository reference instead.
