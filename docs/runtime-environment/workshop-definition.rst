Workshop Definition
===================

The ``Workshop`` custom resource defines a workshop.

The raw custom resource definition for the ``Workshop`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/workshop.yaml

Workshop title and description
------------------------------

Each workshop is required to provide the ``title`` and ``description`` fields. If the fields are not supplied, the ``Workshop`` resource will be rejected when you attempt to load it into the Kubernetes cluster.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
        files: github.com/eduk8s/lab-markdown-sample

The ``title`` field should be a single line value giving the subject of the workshop.

The ``description`` field should be a longer description of the workshop.

The following optional information can also be supplied for the workshop.

.. code-block:: yaml
    :emphasize-lines: 8-16

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      url: https://github.com/eduk8s/lab-markdown-sample
      difficulty: beginner
      duration: 15m
      vendor: eduk8s.io
      authors:
      - John Smith
      tags:
      - template
      logo: data:image/png;base64,....
      content:
        files: github.com/eduk8s/lab-markdown-sample

The ``url`` field should be a URL you can go to for more information about the workshop.

The ``difficulty`` field should give an indication of who the workshop is targeting. The value must be one of ``beginner``, ``intermediate``, ``advanced`` and ``extreme``.

The ``duration`` field gives the expected maximum amount of time the workshop would take to complete. This field only provides informational value and is not used to police how long a workshop instance will last. The format of the field is an integer number with ``s``, ``m``, or ``h`` suffix.

The ``vendor`` field should be a value which identifies the company or organisation which the authors are affiliated with. This could be a company or organisation name, or a DNS hostname under the control of whoever has created the workshop.

The ``authors`` field should list the people who worked on creating the workshop.

The ``tags`` field should list labels which help to identify what the workshop is about. This will be used in a searchable catalog of workshops.

The ``logo`` field should be a graphical image provided in embedded data URI format which depicts the topic of the workshop. The image should be 400 by 400 pixels. This will be used in a searchable catalog of workshops.

Note that when referring to a workshop definition after it has been loaded into a Kubernetes cluster, the value of ``name`` field given in the metadata is used. If you want to play around with slightly different variations of a workshop, copy the original workshop definition YAML file and change the value of ``name``. Then make your changes and load it into the Kubernetes cluster.

Downloading workshop content
----------------------------

Workshop content can be downloaded at the time the workshop instance is created. Provided the amount of content is not too great, this shouldn't affect startup times for the workshop instance. The alternative is to bundle the workshop content in a container image built from the eduk8s workshop base image.

To download workshop content at the time the workshop instance is started, set the ``content.files`` field to the location of the workshop content.

.. code-block:: yaml
    :emphasize-lines: 8-9

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
        files: github.com/eduk8s/lab-markdown-sample

The location can be either a GitHub repository reference, or a URL to a tarball hosted on a HTTP server.

In the case of a GitHub repository, do not prefix the location with ``https://`` as this is a symbolic reference and not an actual URL.

The format of the reference to the GitHub repository is similar to that used with kustomize when referencing GitHub repositories. For example:

* ``github.com/organisation/project`` - Use the workshop content hosted at the root of the Git repository. The ``master`` branch is used.
* ``github.com/organisation/project/subdir?ref=develop`` - Use the workshop content hosted at ``subdir`` of the Git repository. The ``develop`` branch is used.

In the case of a URL to a tarball hosted on a HTTP server, the workshop content is taken from the top level directory of the unpacked tarball. It is not possible to specify a subdirectory within the tarball. This means you cannot use a URL reference to refer to release tarballs which are automatically created by GitHub, as these place content in a subdirectory corresponding to the release name, branch or Git reference. For GitHub repositories, always use the GitHub repository reference instead.

In both cases for downloading workshop content, the ``workshop`` sub directory holding the actual workshop content, will be relocated to ``/opt/workshop`` so that it is not visible to a user. If you want other files ignored and not included in what the user can see, you can supply a ``.eduk8signore`` file in your repository or tarball and list patterns for the files in it.

Note that the contents of the ``.eduk8signore`` file is processed as a list of patterns and each will be applied recursively to subdirectories. To ensure that a file is only ignored if it resides in the root directory, you need to prefix it with ``./``.

.. code-block:: text

    ./.dockerignore
    ./.gitignore
    ./Dockerfile
    ./LICENSE
    ./README.md
    ./kustomization.yaml
    ./resources

Container image for the workshop
--------------------------------

When workshop content is bundled into a container image, the ``content.image`` field should specify the image reference identifying the location of the container image to be deployed for the workshop instance.

.. code-block:: yaml
    :emphasize-lines: 8-9

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
        image: quay.io/eduk8s/lab-markdown-sample:master

Even if using the ability to download workshop content when the workshop environment is started, you may still want to override the workshop image used as a base. This would be done where you have a custom workshop base image that includes additional language runtimes or tools required by specialised workshops.

For example, if running a Java workshop, you could specify the ``jdk11-environment`` workshop image, with workshop content still pulled down from GitHub.

.. code-block:: yaml
    :emphasize-lines: 8-10

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-spring-testing
    spec:
      title: Spring Testing
      description: Playground for testing Spring development
      content:
        image: quay.io/eduk8s/jdk11-environment:master
        files: github.com/eduk8s-tests/lab-spring-testing

Where special custom workshop base images are available as part of the eduk8s project, instead of specifying the full location for the image, including the image registry, you can specify a short name. The eduk8s operator will then fill in the rest of the details.

.. code-block:: yaml
    :emphasize-lines: 8-10

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-spring-testing
    spec:
      title: Spring Testing
      description: Playground for testing Spring development
      content:
        image: jdk11-environment:*
        files: github.com/eduk8s-tests/lab-spring-testing

The short versions of the names which are recognised are:

* ``base-environment:*`` - A tagged version of the ``base-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``base-environment:develop`` - The ``develop`` version of the ``base-environment`` workshop image.
* ``base-environment:master`` - The ``master`` version of the ``base-environment`` workshop image.
* ``jdk8-environment:*`` - A tagged version of the ``jdk8-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``jdk8-environment:develop`` - The ``develop`` version of the ``jdk8-environment`` workshop image.
* ``jdk8-environment:master`` - The ``master`` version of the ``jdk8-environment`` workshop image.
* ``jdk11-environment:*`` - A tagged version of the ``jdk11-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``jdk11-environment:develop`` - The ``develop`` version of the ``jdk11-environment`` workshop image.
* ``jdk11-environment:master`` - The ``master`` version of the ``jdk11-environment`` workshop image.
* ``conda-environment:*`` - A tagged version of the ``conda-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``conda-environment:develop`` - The ``develop`` version of the ``conda-environment`` workshop image.
* ``conda-environment:master`` - The ``master`` version of the ``conda-environment`` workshop image.

The ``*`` variants of the short names map to the most up to date version of the image which was available at the time that the version of the eduk8s operator was released. That version is thus guaranteed to work with that version of the eduk8s operator, where as ``develop`` and ``master`` versions may be newer, with possible incompatibilities. The ``develop`` and ``master`` versions principally exist to allow testing with newer versions.

Note that if required, the short names can be remapped in the ``SystemProfile`` configuration of the eduk8s operator. Additional short names can also be defined which map to your own custom workshop base images for use in your own deployment of the eduk8s operator, along with any workshop of your own.

Setting environment variables
-----------------------------

If you want to set or override environment variables for the workshop instance, you can supply the ``session.env`` field.

.. code-block:: yaml
    :emphasize-lines: 10-13

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
        env:
        - name: REGISTRY_HOST
          value: registry.eduk8s.io

The ``session.env`` field should be a list of dictionaries with ``name`` and ``value`` fields.

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``service_account`` - The name of the service account the workshop instance runs as, and which has access to the namespace created for that workshop instance.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The syntax for referencing one of the parameters is ``$(parameter_name)``.

Note that the ability to override environment variables using this field should be limited to cases where they are required for the workshop. If you want to set or override an environment for a specific workshop environment, use the ability to set environment variables in the ``WorkshopEnvironment`` custom resource for the workshop environment instead.

Overriding the memory available
-------------------------------

By default the container the workshop environment is running in is allocated 512Mi. If the editor is enabled a total of 768Mi is allocated, and if editor plugins are also allocated, it is 1Gi.

Where the purpose of the workshop is mainly aimed at deploying workloads into the Kubernetes cluster, this would generally be sufficient. If you are running workloads in the workshop environment container itself and need more memory, the default can be overridden by setting ``memory`` under ``session.resources``.

.. code-block:: yaml
    :emphasize-lines: 10-12

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
        image: quay.io/eduk8s/lab-markdown-sample:master
      session:
        resources:
          memory: 2Gi

Mounting a persistent volume
----------------------------

In circumstances where a workshop needs persistent storage to ensure no loss of work if the workshop environment container were killed and restarted, you can request a persistent volume be mounted into the workshop container.

.. code-block:: yaml
    :emphasize-lines: 10-12

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
        image: quay.io/eduk8s/lab-markdown-sample:master
      session:
        resources:
          storage: 5Gi

The persistent volume will be mounted on top of the ``/home/eduk8s`` directory. Because this would hide any workshop content bundled with the image, an init container is automatically configured and run, which will copy the contents of the home directory to the persistent volume, before the persistent volume is then mounted on top of the home directory.

Resource budget for namespaces
------------------------------

In conjunction with each workshop instance, a namespace will be created for use during the workshop. That is, from the terminal of the workshop dashboard applications can be deployed into the namespace via the Kubernetes REST API using tools such as ``kubectl``.

By default this namespace will have whatever limit ranges and resource quota which may be enforced by the Kubernetes cluster. In most case this will mean there are no limits or quotas. The exception is likely OpenShift, which through a project template can automatically apply limit ranges and quotas to new namespaces when created.

To control how much resources can be used where no limit ranges and resource quotas are set, or to override any default limit ranges and resource quota, you can set a resource budget for any namespaces created for the workshop instance.

To set the resource budget, set the ``session.budget`` field.

.. code-block:: yaml
    :emphasize-lines: 10-11

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-markdown-sample
    spec:
      title: Markdown Sample
      description: A sample workshop using Markdown
      content:
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

Note that this budget setting and the memory values are distinct from the amount of memory the container the workshop environment runs in. If you need to change how much memory is available to the workshop container, set the ``memory`` setting under ``session.resources``.

Patching workshop deployment
----------------------------

In order to set or override environment variables you can provide ``session.env``. If you need to make other changes to the pod template for the deployment used to create the workshop instance, you need to provide an overlay patch. Such a patch might be used to override the default CPU and memory limit applied to the workshop instance, or to mount a volume.

The patches are provided by setting ``session.patches``. The patch will be applied to the ``spec`` field of the pod template.

.. code-block:: yaml
    :emphasize-lines: 10-18

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-resource-testing
    spec:
      title: Resource testing
      description: Play area for testing memory resources
      content:
        files: github.com/eduk8s-tests/lab-resource-testing
      session:
        patches:
          containers:
          - name: workshop
            resources:
              requests:
                memory: "1Gi"
              limits:
                memory: "1Gi"

In this example the default memory limit of "512Mi" is increased to "1Gi". Although memory is being set via a patch in this example, the ``session.resources.memory`` field is the preferred way to override the memory allocated to the container the workshop environment is running in.

The patch when applied works a bit differently to overlay patches as found elsewhere in Kubernetes. Specifically, when patching an array and the array contains a list of objects, a search is performed on the destination array and if an object already exists with the same value for the ``name`` field, the item in the source array will be overlaid on top of the existing item in the destination array. If there is no matching item in the destination array, the item in the source array will be added to the end of the destination array.

This means an array doesn't outright replace an existing array, but a more intelligent merge is performed of elements in the array.

Creation of session resources
-----------------------------

When a workshop instance is created, the deployment running the workshop dashboard is created in the namespace for the workshop environment. When more than one workshop instance is created under that workshop environment, all those deployments are in the same namespace.

For each workshop instance, a separate empty namespace is created with name corresponding to the workshop session. The workshop instance is configured so that the service account that the workshop instance runs under can access and create resources in the namespace created for that workshop instance. Each separate workshop instance has its own corresponding namespace and they can't see the namespace for another instance.

If you want to pre-create additional resources within the namespace for a workshop instance, you can supply a list of the resources against the ``session.objects`` field within the workshop definition. You might use this to add additional custom roles to the service account for the workshop instance when working in that namespace, or to deploy a distinct instance of an application for just that workshop instance, such as a private image registry.

.. code-block:: yaml
    :emphasize-lines: 10-48

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-registry-testing
    spec:
      title: Registry Testing
      description: Play area for testing image registry
      content:
        files: github.com/eduk8s-tests/lab-registry-testing
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

When resources are created, owner references are added making the ``WorkshopSession`` custom resource corresponding to the workshop instance the owner. This means that when the workshop instance is deleted, any resources will be automatically deleted.

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``service_account`` - The name of the service account the workshop instance runs as, and which has access to the namespace created for that workshop instance.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The syntax for referencing one of the parameters is ``$(parameter_name)``.

In the case of cluster scoped resources, it is important that you set the name of the created resource so that it embeds the value of ``$(session_namespace)``. This way the resource name is unique to the workshop instance and you will not get a clash with a resource for a different workshop instance.

Note that due to shortcomings in the current official Python REST API client for Kubernetes, the way it creates resource objects from an arbitrary resource description means it will fail for custom resources. As a workaround until the Python REST API client is fixed, you need to flag custom resources, and indicate whether they have cluster scope or are namespaced. To do this add an annotation to the metadata for the resource with name ``training.eduk8s.io/objects.crd.scope`` and set it to either ``Cluster`` or ``Namespaced``.

For examples of making use of the available parameters see the following sections.

Overriding default RBAC rules
-----------------------------

By default the service account created for the workshop instance, has ``admin`` role access to the session namespace created for that workshop instance. This enables the service account to be used to deploy applications to the session namespace, as well as manage secrets and service accounts.

Where a workshop doesn't require ``admin`` access for the namespace, you can reduce the level of access it has to ``edit`` or ``view`` by setting the ``session.role`` field.

.. code-block:: yaml
    :emphasize-lines: 10-11

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-role-testing
    spec:
      title: Role Testing
      description: Play area for testing roles
      content:
        files: github.com/eduk8s-tests/lab-role-testing
      session:
        role: view

If you need to add additional roles to the service account, such as the ability to work with custom resource types which have been added to the cluster, you can add the appropriate ``Role`` and ``RoleBinding`` definitions to the ``session.objects`` field described previously.

.. code-block:: yaml
    :emphasize-lines: 10-43

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-kpack-testing
    spec:
      title: Kpack Testing
      description: Play area for testing kpack
      content:
        files: github.com/eduk8s-tests/lab-kpack-testing
      session:
        objects:
        - apiVersion: rbac.authorization.k8s.io/v1
          kind: Role
          metadata:
            name: kpack-user
          rules:
          - apiGroups:
            - build.pivotal.io
            resources:
            - builds
            - builders
            - images
            - sourceresolvers
            verbs:
            - get
            - list
            - watch
            - create
            - delete
            - patch
            - update
        - apiVersion: rbac.authorization.k8s.io/v1
          kind: RoleBinding
          metadata:
            name: kpack-user
          roleRef:
            apiGroup: rbac.authorization.k8s.io
            kind: Role
            name: kpack-user
          subjects:
          - kind: ServiceAccount
            namespace: $(workshop_namespace)
            name: $(service_account)

Because the subject of a ``RoleBinding`` needs to specify the service account name and namespace it is contained within, both of which are unknown in advance, references to parameters for the workshop namespace and service account for the workshop instance are used when defining the subject.

Adding additional resources via ``session.objects`` can also be used to grant cluster level roles, which would be necessary if you need to grant the service account ``cluster-admin`` role.

.. code-block:: yaml
    :emphasize-lines: 10-23

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-admin-testing
    spec:
      title: Admin Testing
      description: Play area for testing cluster admin
      content:
        files: github.com/eduk8s-tests/lab-admin-testing
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

In this case the name of the cluster role binding resource embeds ``$(session_namespace)`` so that its name is unique to the workshop instance and doesn't overlap with a binding for a different workshop instance.

Creating additional namespaces
------------------------------

For each workshop instance a session namespace is created, into which applications can be pre-deployed, or deployed as part of the workshop.

If you need more than one namespace per workshop instance, you can create further namespaces by adding an appropriate ``Namespace`` resource to ``session.objects``.

.. code-block:: yaml
    :emphasize-lines: 10-15

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-namespace-testing
    spec:
      title: Namespace Testing
      description: Play area for testing namespaces
      content:
        files: github.com/eduk8s-tests/lab-namespace-testing
      session:
        objects:
        - apiVersion: v1
          kind: Namespace
          metadata:
            name: $(session_namespace)-apps

When additional namespaces are created, limit ranges and resource quotas will be set as per the resource budget set for the workshop. That is, each namespace has a separate resource budget, it is not shared.

If you need to have a different resource budget set for the additional namespace, you can add the annotation ``training.eduk8s.io/session.budget`` in the ``Namespace`` resource metadata and set the value to the required resource budget.

.. code-block:: yaml
    :emphasize-lines: 10-17

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-namespace-testing
    spec:
      title: Namespace Testing
      description: Play area for testing namespaces
      content:
        files: github.com/eduk8s-tests/lab-namespace-testing
      session:
        objects:
        - apiVersion: v1
          kind: Namespace
          metadata:
            name: $(session_namespace)-apps
            annotations:
              training.eduk8s.io/session.budget: large

If you need more fine grained control over the limit ranges and resource quotas, set the value of the annotation to ``custom`` and add the ``LimitRange`` and ``ResourceQuota`` definitions to ``session.objects``.

In this case you must set the ``namespace`` for the ``LimitRange`` and ``ResourceQuota`` resource to the name of the namespace, e.g., ``$(session_namespace)-apps`` so they are only applied to that namespace.

If you need to override what role the service account for the workshop instance has in the additional namespace, you can set the ``training.eduk8s.io/session.role`` annotation on the ``Namespace`` resource.

.. code-block:: yaml
    :emphasize-lines: 10-17

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-namespace-testing
    spec:
      title: Namespace Testing
      description: Play area for testing namespaces
      content:
        files: github.com/eduk8s-tests/lab-namespace-testing
      session:
        objects:
        - apiVersion: v1
          kind: Namespace
          metadata:
            name: $(session_namespace)-apps
            annotations:
              training.eduk8s.io/session.role: view

If needing to create any other resources within the additional namespace, such as deployments, ensure that the ``namespace`` is set in the ``metadata`` of the resource, e.g., ``$(session_namespace)-apps``.

Shared workshop resources
-------------------------

Adding a list of resources to ``session.objects`` will result in the given resources being created for each workshop instance, where namespaced resources will default to being created in the session namespace for that workshop instance.

If instead you want to have one common shared set of resources created once for the whole workshop environment, that is, used by all workshop instances, you can list them in the ``environment.objects`` field.

This might for example be used to deploy a single image registry which is used by all workshop instances, with a Kubernetes job used to import a set of images into the image registry, which are then referenced by the workshop instances.

For namespaced resources, it is not necessary to specify the ``namespace`` field of the resource ``metadata``. When the ``namespace`` field is not present the resource will automatically be created within the workshop namespace for that workshop environment.

When resources are created, owner references are added making the ``WorkshopEnvironment`` custom resource corresponding to the workshop environment the owner. This means that when the workshop environment is deleted, any resources will be automatically deleted.

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``workshop_name`` - The name of the workshop. This is the name of the ``Workshop`` definition the workshop environment was created against.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``environment_token`` - The value of the token which needs to be used in workshop requests against the workshop environment.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances, and their service accounts, are created. It is the same namespace that shared workshop resources are created.

If you want to create additional namespaces associated with the workshop environment, embed a reference to ``$(workshop_namespace)`` in the name of the additional namespaces, with an appropriate suffix. Be mindful that the suffix doesn't overlap with the range of session IDs for workshop instances.

Overriding pod security policy
------------------------------

The pod for the workshop session will be setup with a pod security policy which restricts what can be done from containers in the pod. The nature of the applied pod security policy will be adjusted when enabling support for doing docker builds to enable the ability to do docker builds inside the side car container attached to the workshop container.

If you are customising the workshop by patching the pod specification using ``session.patches``, in order to add your own side car container, and that side car container needs a custom pod security policy which you define in ``environment.objects`` or ``session.objects``, you will need to disable the application of the pod security policy done by the eduk8s operator. This can be done by setting ``session.security.policy`` to ``custom``.

.. code-block:: yaml
    :emphasize-lines: 10-12

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-policy-testing
    spec:
      title: Policy Testing
      description: Play area for testing policy override
      content:
        files: github.com/eduk8s-tests/lab-policy-testing
      session:
        security:
          policy: custom
        objects:
        - apiVersion: rbac.authorization.k8s.io/v1
          kind: RoleBinding
          metadata:
            namespace: $(workshop_namespace)
            name: $(session_namespace)-podman
          roleRef:
            apiGroup: rbac.authorization.k8s.io
            kind: ClusterRole
            name: $(workshop_namespace)-podman
          subjects:
          - kind: ServiceAccount
            namespace: $(workshop_namespace)
            name: $(service_account)
      environment:
        objects:
        - apiVersion: policy/v1beta1
          kind: PodSecurityPolicy
          metadata:
            name: aaa-$(workshop_namespace)-podman
          spec:
            privileged: true
            allowPrivilegeEscalation: true
            requiredDropCapabilities:
            - KILL
            - MKNOD
            hostIPC: false
            hostNetwork: false
            hostPID: false
            hostPorts: []
            runAsUser:
              rule: MustRunAsNonRoot
            seLinux:
              rule: RunAsAny
            fsGroup:
              rule: RunAsAny
            supplementalGroups:
              rule: RunAsAny
            volumes:
            - configMap
            - downwardAPI
            - emptyDir
            - persistentVolumeClaim
            - projected
            - secret
        - apiVersion: rbac.authorization.k8s.io/v1
          kind: ClusterRole
          metadata:
            name: $(workshop_namespace)-podman
          rules:
          - apiGroups:
            - policy
            resources:
            - podsecuritypolicies
            verbs:
            - use
            resourceNames:
            - aaa-$(workshop_namespace)-podman

By overriding the pod security policy you are responsible for limiting what can be done from the workshop pod. In other words, you should only add just the extra capabilities you need. The pod security policy will only be applied to the pod the workshop session runs in, it does not affect any pod security policy applied to service accounts which exist in the session namespace or other namespaces which have been created.

Note that due to a lack of a good way to deterministically determine priority of applied pod security policies when a default pod security policy has been applied globally by mapping it to the ``system:authenticated`` group, with priority instead falling back to ordering of the names of the pod security policies, it is recommend you use ``aaa-`` as a prefix to the custom pod security name you create. This will ensure that it take precedence over any global default pod security policy such as ``restricted``, ``pks-restricted`` or ``vmware-system-tmc-restricted``, no matter what the name of the global policy default is called.

Defining additional ingress points
----------------------------------

If running additional background applications, by default they are only accessible to other processes within the same container. In order for an application to be accessible to a user via their web browser, an ingress needs to be created mapping to the port for the application.

You can do this by supplying a list of the ingress points, and the internal container port they map to, by setting the ``session.ingresses`` field in the workshop definition.

.. code-block:: yaml
    :emphasize-lines: 10-13

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        ingresses:
        - name: application
          port: 8080

The form of the hostname used in URL to access the service will be:

.. code-block:: text

    $(session_namespace)-application.$(ingress_domain)

Note that you should not use as the name of any additional dashboards, ``terminal``, ``console``, ``slides`` or ``editor``. These are reserved for the corresponding builtin capabilities providing those features.

Accessing the service will be protected by any access controls enforced by the workshop environment or training portal. If the training portal is used this should be transparent, otherwise you will need to supply any login credentials for the workshop again when prompted by your web browser.

Enabling the Kubernetes console
-------------------------------

By default the Kubernetes console is not enabled. If you want to enable it and make it available through the web browser when accessing a workshop, you need to add a ``session.applications.console`` section to the workshop definition, and set the ``enabled`` property to ``true``.

.. code-block:: yaml
    :emphasize-lines: 11-13

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          console:
            enabled: true

The Kubernetes dashboard provided by the Kubernetes project will be used. If you would rather use Octant as the console, you can set the ``vendor`` property to ``octant``.

.. code-block:: yaml
    :emphasize-lines: 11-14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          console:
            enabled: true
            vendor: octant

When ``vendor`` is not set, ``kubernetes`` is assumed.

If a workshop is designed such that it can only be run on OpenShift, and you wish to use the OpenShift web console, you can set vendor to ``openshift``.

.. code-block:: yaml
    :emphasize-lines: 11-14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          console:
            enabled: true
            vendor: openshift

In just the case of the OpenShift web console, if you need to override the default version of the OpenShift web console used, you can set the ``openshift.version`` sub property.

.. code-block:: yaml
    :emphasize-lines: 15-16

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          console:
            enabled: true
            vendor: openshift
            openshift:
              version: "4.3"

Ensure that you add quotes around the version number so that it is interpreted as a string.

The source of the container image for the OpenShift web console will be ``quay.io/openshift/origin-console``. If you want to use a container image for the OpenShift web console which is hosted elsewhere, you can set the ``openshift.image`` sub property.

.. code-block:: yaml
    :emphasize-lines: 15-16

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          console:
            enabled: true
            vendor: openshift
            openshift:
              image: quay.io/openshift/origin-console:4.3

Note that the OpenShift web console will not be fully functional if deployed to a Kubernetes cluster other than OpenShift as it is dependent on resource types only found in OpenShift.

Even on OpenShift, the web console may not be fully functional due to the restrictive RBAC in place for a workshop session. This is because the OpenShift web console is usually deployed global to the cluster and with elevated role access. You may be able to unlock some extra capabilities of the OpenShift web console if you can identify any additional roles that need to be granted to the service account used by the workshop environment, and enable access by adding appropriate ``Role`` or ``RoleBinding`` resources to the workshop definition.

Enabling the integrated editor
------------------------------

By default the integrated web based editor is not enabled. If you want to enable it and make it available through the web browser when accessing a workshop, you need to add a ``session.applications.editor`` section to the workshop definition, and set the ``enabled`` property to ``true``.

.. code-block:: yaml
    :emphasize-lines: 11-13

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          editor:
            enabled: true

The integrated editor used is Theia. Although Theia supports plugins, a search for local plugins installed with the editor is not enabled by default. This is because of the extra memory requirements from running the plugins. To enable the builtin plugins set the ``applications.editor.plugins.enabled`` property to ``true``.

.. code-block:: yaml
    :emphasize-lines: 11-12,16-17

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        resources:
          memory: 1Gi
        applications:
          editor:
            enabled: true
            plugins:
              enabled: true

Because of extra memory resources required, you would generally want to increase the amount of memory used by the workshop session environment.

If you want to use additional editor plugins, they can be installed from the editor, or you can include them with the workshop content, or specify them in the workshop definition.

When including the plugins in the workshop content, they need to have been installed under the ``workshop/theia/plugins`` directory. If listing them in the workshop definition list them under the ``applications.editor.plugins.install`` property:

.. code-block:: yaml
    :emphasize-lines: 18-23

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        resources:
          memory: 1Gi
        applications:
          editor:
            enabled: true
            plugins:
              enabled: true
              install:
              - "https://github.com/redhat-developer/vscode-java/releases/download/v0.54.2/redhat.java-0.54.2.vsix"
              - "https://github.com/microsoft/vscode-java-debug/releases/download/0.24.0/vscjava.vscode-java-debug-0.24.0.vsix"
              - "https://github.com/microsoft/vscode-java-test/releases/download/0.22.0/vscjava.vscode-java-test-0.22.0.vsix"
              - "https://github.com/microsoft/vscode-java-dependency/releases/download/0.6.0/vscode-java-dependency-0.6.0.vsix"
              - "https://s3-us-west-1.amazonaws.com/s3-test.spring.io/sts4/vscode-extensions/snapshots/vscode-spring-boot-1.18.0-202005071819.vsix"

Note that although additional plugins are listed here for Java, if you use the dedicated Java environment base images, these will already be pre-installed and you do not need to add them yourself.

Enabling session image registry
-------------------------------

Workshops using tools such as ``kpack`` or ``tekton`` and which need a place to push container images when built, can enable an image registry. A separate image registry is deployed for each workshop session.

Note that the image registry is only currently fully usable if workshops are deployed under an eduk8s operator configuration which uses secure ingress. This is because an insecure registry would not be trusted by the Kubernetes cluster as the source of container images when doing deployments.

To enable the deployment of an image registry per workshop session you need to add a ``session.applications.registry`` section to the workshop definition, and set the ``enabled`` property to ``true``.

.. code-block:: yaml
    :emphasize-lines: 11-13

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          registry:
            enabled: true

The image registry will mount a persistent volume for storing of images. By default the size of that persistent volume is 5Gi. If you need to override the size of the persistent volume add the ``storage`` property under the ``registry`` section.

.. code-block:: yaml
    :emphasize-lines: 14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          registry:
            enabled: true
            storage: 20Gi

The amount of memory provided to the image registry will default to 768Mi. If you need to increase this, add the ``memory`` property under the ``registry`` section.

.. code-block:: yaml
    :emphasize-lines: 14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          registry:
            enabled: true
            memory: 1Gi

The image registry will be secured with a username and password unique to the workshop session and expects access over a secure connection.

To allow access from the workshop session, the file ``$HOME/.docker/config.json`` containing the registry credentials will be injected into the workshop session. This will be automatically used by tools such as ``docker``. For tools running in Kubernetes, you will need to create an appropriate secret for that tool which contains the configuration file.

If you need access to the raw registry host details and credentials, they are provided as environment variables in the workshop session. The environment variables are:

* ``REGISTRY_HOST`` - Contains the host name for the image registry for the workshop session.
* ``REGISTRY_AUTH_FILE`` - Contains the location of the ``docker`` configuration file. Should always be the equivalent of ``$HOME/.docker/config.json``.
* ``REGISTRY_USERNAME`` - Contains the username for accessing the image registry.
* ``REGISTRY_PASSWORD`` - Contains the password for accessing the image registry. This will be different for each workshop session.

The URL for accessing the image registry adopts the HTTP protocol scheme inherited from the environment variable ``INGRESS_PROTOCOL``. This would be the same HTTP protocol scheme as the workshop sessions themselves use.

If you need to use any of the environment variables related to the image registry as data variables in workshop content, you will need to declare this in the ``workshop/modules.yaml`` file in the ``config.vars`` section.

.. code-block:: yaml

    config:
      vars:
      - name: REGISTRY_HOST
      - name: REGISTRY_AUTH_FILE
      - name: REGISTRY_USERNAME
      - name: REGISTRY_PASSWORD

Enabling ability to use docker
------------------------------

If you need to be able to build container images in a workshop using ``docker``, it needs to be enabled first. Each workshop session will be provided with its own separate docker daemon instance running in a container.

Note that enabling of support for running ``docker`` requires the use of a privileged container for running the docker daemon. Because of the security implications of providing access to docker with this configuration, it is strongly recommended that if you don't trust the people doing the workshop, any workshops which require docker only be hosted in a disposable Kubernetes cluster which is destroyed at the completion of the workshop. You should never enable docker for workshops hosted on a public service which is always kept running and where arbitrary users could access the workshops.

To enable support for being able to use ``docker`` add a ``session.applications.docker`` section to the workshop definition, and set the ``enabled`` property to ``true``.

.. code-block:: yaml
    :emphasize-lines: 11-13

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          docker:
            enabled: true

The container which runs the docker daemon will mount a persistent volume for storing of images which are pulled down or built locally. By default the size of that persistent volume is 5Gi. If you need to override the size of the persistent volume add the ``storage`` property under the ``docker`` section.

.. code-block:: yaml
    :emphasize-lines: 14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          docker:
            enabled: true
            storage: 20Gi

The amount of memory provided to the container running the docker daemon will default to 768Mi. If you need to increase this, add the ``memory`` property under the ``registry`` section.

.. code-block:: yaml
    :emphasize-lines: 14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          docker:
            enabled: true
            memory: 1Gi

Access to the docker daemon from the workshop session uses a local UNIX socket shared with the container running the docker daemon. If using a local tool which wants to access the socket connection for the docker daemon directly rather than by running ``docker``, it should use the ``DOCKER_HOST`` environment variable to determine the location of the socket.

The docker daemon is only available from within the workshop session and cannot be accessed outside of the pod by any tools deployed separately to Kubernetes.

Enabling WebDAV access to files
-------------------------------

Local files within the workshop session can be accessed or updated from the terminal command line or editor of the workshop dashboard. The local files reside in the filesystem of the container the workshop session is running in.

If there is a need to be able to access the files remotely, it is possible to enable WebDAV support for the workshop session.

To enable support for being able to access files over WebDAV add a ``session.applications.webdav`` section to the workshop definition, and set the ``enabled`` property to ``true``.

.. code-block:: yaml
    :emphasize-lines: 11-13

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          webdav:
            enabled: true

The result of this will be that a WebDAV server will be run within the workshop session environment. A set of credentials will also be automatically generated which are available as environment variables. The environment variables are:

* ``WEBDAV_USERNAME`` - Contains the username which needs to be used when authenticating over WebDAV.
* ``WEBDAV_PASSWORD`` - Contains the password which needs to be used authenticating over WebDAV.

If you need to use any of the environment variables related to the image registry as data variables in workshop content, you will need to declare this in the ``workshop/modules.yaml`` file in the ``config.vars`` section.

.. code-block:: yaml

    config:
      vars:
      - name: WEBDAV_USERNAME
      - name: WEBDAV_PASSWORD

The URL endpoint for accessing the WebDAV server is the same as the workshop session, with ``/webdav/`` path added. This can be constructed from the terminal using:

::

    $INGRESS_PROTOCOL://$SESSION_NAMESPACE.$INGRESS_DOMAIN/webdav/

In workshop content it can be constructed using:

::

    {{ingress_protocol}}://{{session_namespace}}.{{ingress_domain}}/webdav/

You should be able to use WebDAV client support provided by your operating system, of by using a standalone WebDAV client such as `CyberDuck <https://cyberduck.io/>`_.

Using WebDAV can make it easier if you need to transfer files to or from the workshop session.

Customizing the terminal layout
-------------------------------

By default a single terminal is provided in the web browser when accessing the workshop. If required, you can enable alternate layouts which provide additional terminals. To set the layout, you need to add the ``session.applications.terminal`` section and include the ``layout`` property with the desired layout.

.. code-block:: yaml
    :emphasize-lines: 11-14

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        applications:
          terminal:
            enabled: true
            layout: split

The options for the ``layout`` property are:

* ``default`` - Single terminal.
* ``split`` - Two terminals stacked above each other in ratio 60/40.
* ``split/2`` - Three terminals stacked above each other in ration 50/25/25.

When adding the ``terminal`` section, you must include the ``enabled`` property and set it to ``true`` as it is a required field when including the section.

Adding custom dashboard tabs
----------------------------

Exposed applications, and external sites, can be given their own custom dashboard tab. This is done by specifying the list of dashboard panels and the target URL.

.. code-block:: yaml
    :emphasize-lines: 14-18

    apiVersion: training.eduk8s.io/v1alpha2
    kind: Workshop
    metadata:
      name: lab-application-testing
    spec:
      title: Application Testing
      description: Play area for testing my application
      content:
        image: quay.io/eduk8s-tests/lab-application-testing:master
      session:
        ingresses:
        - name: application
          port: 8080
        dashboards:
        - name: Application
          url: "$(ingress_protocol)://$(session_namespace)-application.$(ingress_domain)/"
        - name: Example
          url: http://www.example.com

The URL values can reference a number of pre-defined parameters. The available parameters are:

* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The URL can reference an external web site, however, that web site must not prohibit being embedded in a HTML iframe.
