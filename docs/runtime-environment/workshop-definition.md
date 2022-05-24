Workshop Definition
===================

The ``Workshop`` custom resource defines a workshop.

The raw custom resource definition for the ``Workshop`` custom resource can be viewed by running:

```
kubectl get crd/workshops.training.educates.dev -o yaml
```

Workshop title and description
------------------------------

Each workshop is required to provide the ``title`` and ``description`` fields. If the fields are not supplied, the ``Workshop`` resource will be rejected when you attempt to load it into the Kubernetes cluster.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
```

The ``title`` field should be a single line value giving the subject of the workshop.

The ``description`` field should be a longer description of the workshop.

The following optional information can also be supplied for the workshop.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  url: https://github.com/vmware-tanzu-labs/lab-markdown-sample
  difficulty: beginner
  duration: 15m
  vendor: educates.dev
  authors:
  - John Smith
  tags:
  - template
  logo: data:image/png;base64,....
```

The ``url`` field should be a URL you can go to for more information about the workshop.

The ``difficulty`` field should give an indication of who the workshop is targeting. The value must be one of ``beginner``, ``intermediate``, ``advanced`` and ``extreme``.

The ``duration`` field gives the expected maximum amount of time the workshop would take to complete. This field only provides informational value and is not used to police how long a workshop instance will last. The format of the field is an integer number with ``s``, ``m``, or ``h`` suffix.

The ``vendor`` field should be a value which identifies the company or organization which the authors are affiliated with. This could be a company or organization name, or a DNS hostname under the control of whoever has created the workshop.

The ``authors`` field should list the people who worked on creating the workshop.

The ``tags`` field should list labels which help to identify what the workshop is about. This might be used in a searchable catalog of workshops.

The ``logo`` field should be a graphical image provided in embedded data URI format which depicts the topic of the workshop. The image should be 400 by 400 pixels. This might be used in a searchable catalog of workshops.

Note that when referring to a workshop definition after it has been loaded into a Kubernetes cluster, the value of ``name`` field given in the metadata is used. If you want to play around with slightly different variations of a workshop, copy the original workshop definition YAML file and change the value of ``name``. Then make your changes and load it into the Kubernetes cluster.

(downloading-workshop-content)=
Downloading workshop content
----------------------------

Workshop content can be downloaded at the time the workshop instance is created with it being overlayed on a selected workshop base image, or the workshop content can be added into a container image built from a workshop base image.

To download workshop content when a workshop instance starts up, the ``vendir`` tool from Carvel is used. The configuration for ``vendir`` should be included under ``spec.workshop.files``. The format of configuration supplied needs to match the [configuration](https://carvel.dev/vendir/docs/v0.25.0/vendir-spec/) that can be supplied under ``directories.contents`` of the ``Config`` resource used by ``vendir``.

The ``vendir`` tool supports a range of sources for downloading content, including:

* OCI image artefacts stored in an image repository.
* A hosted Git source repository, such as GitHub and Gitlab.
* Inline file definitions and files sourced from Kubernetes secrets.
* Files associated with a GitHub repository release.
* Files downloading from a HTTP web server.

If bundling workshop content into a container image built from a workshop base image, the location of the image can be specified by setting ``spec.workshop.image``.

(hosting-on-an-image-repository)=
Hosting on an image repository
------------------------------

The preferred method for hosting workshop content is to create an OCI image artefact containing the workshop content and host it on an image repository. If this method is used, it will make it possible later to bundle up workshops, relocate them, and use them in disconnected environments.

If you use the workshop templates provided by the Educates project and are using GitHub to store your workshop files, the GitHub action created by the workshop template will automatically create the required OCI image artefact each time you tag the GitHub repository with a specific version, and publish it to the GitHub container registry. The GitHub action will also automatically create a GitHub release with the workshop definition attached, which has been rewritten so that the published OCI image artefact is used.

The initial format of ``spec.workshop.files`` created from the workshop templates will be:

```yaml
spec:
  workshop:
    files:
    - image:
        url: $(image_repository)/{name}-files:latest
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

The ``$(image_repository)`` data variable reference in the ``workshop.files.image.url`` property is special to the workflow for working on workshop content using the local Educates environment discussed in the getting started section of the documentation. This will be rewritten by the GitHub action when a workshop is published, with it replaced with an explicit reference to the GitHub container registry organization used to publish the OCI image artefact containing the workshop content.

The ``{name}`` reference in the same property, in the case of using GitHub and relying on the supplied GitHub actions to publish the workshop content, must be the name of the Git repository. If creating the initial workshop content using the workshop templates, this will be set for you. For the GitHub action to work the ``-files`` suffix to the name must also be used, with it distinguishing the OCI image artefact as being for the workshop content files, as distinct from a custom workshop image for the same workshop.

If not using the workshop templates, local Educates environment, or relying on the GitHub actions workshop to publish the workshop content, but want to use an OCI image artefact to publish the workshop content, set the ``workshop.files.image.url`` property to the location of where you have published the OCI image artefact.

As ``vendir`` is used to download and unpack the OCI image artefact, under ``workshop.files`` for the ``image`` source type you can also supply additional options, including:

* ``includePaths`` - Specify what paths should be included from the OCI image artefact when unpacking.
* ``excludePaths`` - Specify what paths should be excluded from the OCI image artefact when unpacking.
* ``newRootPath`` - Specify the directory path within the OCI image artefact that should be used as the root for the workshop files.

For more details and other options see the ``vendir`` [documentation](https://carvel.dev/vendir/docs/v0.27.0/vendir-spec/).

(hosting-using-a-git-repository)=
Hosting using a Git repository
------------------------------

If not using GitHub, don't want to rely on the GitHub actions for publishing workshop content as an OCI image artefact, or just don't want to deal with OCI image artefacts as a publishing mechanism for workshop content, you can instead configure workshop content to be downloaded from a hosted Git repository.

The format of ``spec.workshop.files`` for downloading workshop content in this case would be:

```yaml
spec:
  workshop:
    files:
    - git:
        url: https://github.com/{organization}/{repository}
        ref: origin/main
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

If not using GitHub, but another Git repository service such as GitLab or a self hosted enterprise version of a Git hosting service, replace ``github.com`` with the hostname of your Git server.

The ``{organization}`` reference in the ``workshop.files.git.url`` property should be replaced with the name of your account or the organization being used. The ``{repository}`` reference should be replaced with the name of Git repository. You must specify ``workshop.files.git.ref`` with an appropriate Git reference. This can describe a branch, commit, or tag.

As ``vendir`` is used to download files from the Git repository, under ``workshop.files`` for the ``git`` source type you can also supply additional options, including:

* ``includePaths`` - Specify what paths should be included from the Git repository when unpacking.
* ``excludePaths`` - Specify what paths should be excluded from the Git repository when unpacking.
* ``newRootPath`` - Specify the directory path within the Git repository that should be used as the root for the workshop files.

For more details and other options see the ``vendir`` [documentation](https://carvel.dev/vendir/docs/v0.27.0/vendir-spec/).

Content download (deprecated)
-----------------------------

Downloading workshop content using ``workshop.files`` is a new mechanism which replaces a now deprecated older mechanism using ``content.files``. Use of ``vendir`` provides greater flexibility and more options for where workshop content can be downloaded. There are a still a few corner cases where ``vendir`` can't be used to replace the older way of downloading content. Issues have been raised against ``vendir`` to have these shortcomings fixed, but in the interm you can still use ``content.files`` if necessary.

To download workshop content using ``content.files`` set the field to the location of the workshop content.

```yaml
spec:
  content:
    files: github.com/vmware-tanzu-labs/lab-markdown-sample
```

The location can be a GitHub or GitLab repository reference, a URL to a tarball hosted on a HTTP server, or a reference to an OCI image artifact on a registry.

In the case of a GitHub or GitLab repository, do not prefix the location with ``https://`` as a symbolic reference is being used and not an actual URL.

The format of the reference to a GitHub or GitLab repository is similar to that used with kustomize when referencing remote repositories. For example:

* ``github.com/organization/project`` - Use the workshop content hosted at the root of the GitHub repository. The ``master`` or ``main`` branch is used.
* ``github.com/organization/project/subdir?ref=develop`` - Use the workshop content hosted at ``subdir`` of the GitHub repository. The ``develop`` branch is used.
* ``gitlab.com/organization/project`` - Use the workshop content hosted at the root of the GitLab repository. The ``master`` branch is used.
* ``gitlab.com/organization/project/subdir?ref=develop`` - Use the workshop content hosted at ``subdir`` of the GitLab repository. The ``develop`` branch is used.

In the case of a URL to a tarball hosted on a HTTP server, the URL can be in the following formats:

* ``https://example.com/workshop.tar`` - Use the workshop content from the top level directory of the unpacked tarball.
* ``https://example.com/workshop.tar.gz`` - Use the workshop content from the top level directory of the unpacked tarball.
* ``https://example.com/workshop.tar?path=subdir`` - Use the workshop content from the specified sub directory path of the unpacked tarball.
* ``https://example.com/workshop.tar.gz?path=subdir`` - Use the workshop content from the specified sub directory path of the unpacked tarball.

The tarball referenced by the URL can be uncompressed or compressed.

If using GitHub, instead of using the earlier form for referencing the Git repository containing the workshop content, you can instead use a URL to refer directly to the downloadable tarball for a specific version of the Git repository.

* ``https://github.com/organization/project/archive/develop.tar.gz?path=project-develop``

When using this form you must reference the ``.tar.gz`` download and cannot use the ``.zip`` file. The base name of the tarball file is the branch or commit name. You must specify the ``path`` query string parameter where the argument is the name of the project and branch or commit. The path needs to be supplied as the contents of the repository is not returned at the root of the archive.

If using GitLab, it also provides a means of download a package as a tarball.

* ``https://gitlab.com/organization/project/-/archive/develop/project-develop.tar.gz?path=project-develop``

For HTTP servers which need HTTP basic authentication, credentials can be provided in the URL:

* ``https://username@token:example.com/workshop.tar.gz``

Be aware that these credentials will be visible to a workshop user. When working with sources of workshop content that require authentication you should use ``content.downloads`` instead.

The last case is a reference to an OCI image artifact stored on a registry. This is not a full container image with operating system, but an image containing just the files making up the workshop content. The URI formats for this is:

* ``imgpkg+https://harbor.example.com/organization/project:version`` - Use the workshop content from the top level directory of the unpacked OCI artifact. The registry in this case must support ``https``.
* ``imgpkg+https://harbor.example.com/organization/project:version?path=subdir`` - Use the workshop content from the specified sub directory path of the unpacked OCI artifact. The registry in this case must support ``https``.
* ``imgpkg+http://harbor.example.com/organization/project:version`` - Use the workshop content from the top level directory of the unpacked OCI artifact. The registry in this case can support only ``http``.
* ``imgpkg+http://harbor.example.com/organization/project:version?path=subdir`` - Use the workshop content from the specified sub directory path of the unpacked OCI artifact. The registry in this case can support only ``http``.

Instead of the prefix ``imgpkg+https://``, you can instead use just ``imgpkg://``. The registry in this case must still support ``https``.

For any of the formats, credentials can be supplied as part of the URI.

* ``imgpkg+https://username:password@harbor.example.com/organization/project:version``

Access to the registry using a secure connection using ``https`` must have a valid certificate, except for the case where the registry uses a ``.local`` address.

As with supplying credentials to HTTP servers, these credentials will be visible to the workshop users.

In all cases for downloading workshop content using ``content.files`` if you want files to be ignored and not included in what the user can see, you can supply a ``.eduk8signore`` file in your repository or tarball and list patterns for the files in it.

Note that the contents of the ``.eduk8signore`` file is processed as a list of patterns and each will be applied recursively to subdirectories. To ensure that a file is only ignored if it resides in the root directory, you need to prefix it with ``./``.

```text
./.dockerignore
./.gitignore
./Dockerfile
./LICENSE
./README.md
./kustomization.yaml
./resources
```

Container image for the workshop
--------------------------------

When using a custom workshop base image, the ``workshop.image`` field should specify the image reference identifying the location of the container image to be deployed for the workshop instance.

If you are making use of the local Educates environment when creating workshop content, and subsequently using GitHub to host your workshop content, and GitHub actions to publish the workshop, this should be specified in the form:

```yaml
spec:
  workshop:
    image: $(image_repository)/{name}-image:latest
    files:
    - image:
        url: $(image_repository)/{name}-files:latest
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

As for ``workshop.files.image.url``, the ``$(image_repository)`` data variable reference in the ``workshop.image`` property is special to the workflow for working on workshop content using the local Educates environment discussed in the getting started section of the documentation. This will be rewritten by the GitHub action when a custom workshop base image is published, with it replaced with an explicit reference to the GitHub container registry organization used to publish the custom workshop image.

The ``{name}`` reference in the same property, in the case of using GitHub and relying on the supplied GitHub actions to publish the workshop content, must be the name of the Git repository. For the GitHub action to work the ``-image`` suffix to the name must also be used, with it distinguishing the custom workshop base image, as being distinct from an OCI image artefact containing just the workshop content.

If not using the workflow provided by using the local Educates environment and the GitHub actions when hosting workshop content on GitHub, ``workshop.images`` should be set to wherever you are hosting the custom workshop base image.

```yaml
spec:
  workshop:
    image: ghcr.io/{organization}/{image}:latest
```

Note that if you use any of the version tags ``:main``, ``:master``, ``:develop`` and ``:latest``, the Educates operator will set the image pull policy to ``Always`` to ensure that a newer version is always pulled if available, otherwise the image will be cached on the Kubernetes nodes and only pulled when it is initially not present. Any other version tags will always be assumed to be unique and never updated. Do though be aware of image registries which use a CDN as front end. When using these image tags the CDN can still always regard them as unique and they will not do pull through requests to update an image even if it uses a tag of ``:latest``.

Where special custom workshop base images are available as part of the Educates project, instead of specifying the full location for the image, including the image registry, you can specify a short name. The Educates operator will then fill in the rest of the details.

```yaml
spec:
  workshop:
    image: jdk11-environment:*
    files:
    - image:
        url: $(image_repository)/{name}-files:latest
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

The short versions of the names which are recognised are:

* ``base-environment:*`` - A tagged version of the ``base-environment`` workshop image which has been matched with the current version of the Educates operator.
* ``jdk8-environment:*`` - A tagged version of the ``jdk8-environment`` workshop image which has been matched with the current version of the Educates operator.
* ``jdk11-environment:*`` - A tagged version of the ``jdk11-environment`` workshop image which has been matched with the current version of the Educates operator.
* ``conda-environment:*`` - A tagged version of the ``conda-environment`` workshop image which has been matched with the current version of the Educates operator.

Note that in older versions of Educates the location of the custom workshop base image could be specified using ``content.image``. This is now deprecated and ``workshop.image`` should always be used.

Setting environment variables
-----------------------------

If you want to set or override environment variables for the workshop instance, you can supply the ``session.env`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  content:
    files: github.com/vmware-tanzu-labs/lab-markdown-sample
  session:
    env:
    - name: REPOSITORY_URL
      value: https://github.com/vmware-tanzu-labs/lab-markdown-sample
```

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

By default the container the workshop environment is running in is allocated 512Mi. If the editor is enabled a total of 1Gi is allocated.

Where the purpose of the workshop is mainly aimed at deploying workloads into the Kubernetes cluster, this would generally be sufficient. If you are running workloads in the workshop environment container itself and need more memory, the default can be overridden by setting ``memory`` under ``session.resources``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-markdown-sample:master
  session:
    resources:
      memory: 2Gi
```

Mounting a persistent volume
----------------------------

In circumstances where a workshop needs persistent storage to ensure no loss of work if the workshop environment container were killed and restarted, you can request a persistent volume be mounted into the workshop container.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-markdown-sample:master
  session:
    resources:
      storage: 5Gi
```

The persistent volume will be mounted on top of the ``/home/eduk8s`` directory. Because this would hide any workshop content bundled with the image, an init container is automatically configured and run, which will copy the contents of the home directory to the persistent volume, before the persistent volume is then mounted on top of the home directory.

Resource budget for namespaces
------------------------------

In conjunction with each workshop instance, a namespace will be created for use during the workshop. That is, from the terminal of the workshop dashboard applications can be deployed into the namespace via the Kubernetes REST API using tools such as ``kubectl``.

By default this namespace will have whatever limit ranges and resource quota may be enforced by the Kubernetes cluster. In most case this will mean there are no limits or quotas. The exception is likely OpenShift, which through a project template can automatically apply limit ranges and quotas to new namespaces when created.

To control how much resources can be used where no limit ranges and resource quotas are set, or to override any default limit ranges and resource quota, you can set a resource budget for any namespaces created for the workshop instance.

To set the resource budget, set the ``session.namespaces.budget`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-markdown-sample:master
  session:
    namespaces:
      budget: small
```

The resource budget sizings and quotas for CPU and memory are:

```text
| Budget    | CPU   | Memory |
|-----------|-------|--------|
| small     | 1000m | 1Gi    |
| medium    | 2000m | 2Gi    |
| large     | 4000m | 4Gi    |
| x-large   | 8000m | 8Gi    |
| xx-large  | 8000m | 12Gi   |
| xxx-large | 8000m | 16Gi   |
```

A value of 1000m is equivalent to 1 CPU.

Separate resource quotas for CPU and memory are applied for terminating and non terminating workloads.

Only the CPU and memory quotas are listed above, but limits are also in place on the number of resource objects that can be created of certain types, including persistent volume claims, replication controllers, services and secrets.

For each budget type, a limit range is created with fixed defaults. The limit ranges for CPU usage on a container are as follows.

```text
| Budget    | Min | Max   | Request | Limit |
|-----------|-----|-------|---------|-------|
| small     | 50m | 1000m | 50m     | 250m  |
| medium    | 50m | 2000m | 50m     | 500m  |
| large     | 50m | 4000m | 50m     | 500m  |
| x-large   | 50m | 8000m | 50m     | 500m  |
| xx-large  | 50m | 8000m | 50m     | 500m  |
| xxx-large | 50m | 8000m | 50m     | 500m  |
```

Those for memory are:

```text
| Budget    | Min  | Max  | Request | Limit |
|-----------|------|------|---------|-------|
| small     | 32Mi | 1Gi  | 128Mi   | 256Mi |
| medium    | 32Mi | 2Gi  | 128Mi   | 512Mi |
| large     | 32Mi | 4Gi  | 128Mi   | 1Gi   |
| x-large   | 32Mi | 8Gi  | 128Mi   | 2Gi   |
| xx-large  | 32Mi | 12Gi | 128Mi   | 2Gi   |
| xxx-large | 32Mi | 16Gi | 128Mi   | 2Gi   |
```

The request and limit values are the defaults applied to a container when no resources specification is given in a pod specification.

If a budget sizing for CPU and memory is sufficient, but you need to override the limit ranges and defaults for request and limit values when none is given in a pod specification, you can supply overrides in ``session.namespaces.limits``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-markdown-sample:master
  session:
    namespaces:
      budget: medium
      limits:
        min:
          cpu: 50m
          memory: 32Mi
        max:
          cpu: 1
          memory: 1Gi
        defaultRequest:
          cpu: 50m
          memory: 128Mi
        default:
          cpu: 500m
          memory: 1Gi
```

Although all possible properties that can be set are listed in this example, you only need to supply the property for the value you want to override.

If you need more control over limit ranges and resource quotas, you should set the resource budget to ``custom``. This will remove any default limit ranges and resource quota which might be applied to the namespace. You can then specify your own ``LimitRange`` and ``ResourceQuota`` resources as part of the list of resources created for each session.

Before disabling the quota and limit ranges, or contemplating any switch to using a custom set of ``LimitRange`` and ``ResourceQuota`` resources, consider if that is what is really required. The default requests defined by these for memory and CPU are fallbacks only. In most cases instead of changing the defaults, you should specify memory and CPU resources in the pod template specification of your deployment resources used in the workshop, to indicate what the application actually requires. This will allow you to control exactly what the application is able to use and so fit into the minimum quota required for the task.

Note that this budget setting and the memory values are distinct from the amount of memory the container the workshop environment runs in. If you need to change how much memory is available to the workshop container, set the ``memory`` setting under ``session.resources``.

Patching workshop deployment
----------------------------

In order to set or override environment variables you can provide ``session.env``. If you need to make other changes to the pod template for the deployment used to create the workshop instance, you need to provide an overlay patch. Such a patch might be used to override the default CPU and memory limit applied to the workshop instance, or to mount a volume.

The patches are provided by setting ``session.patches``. The patch will be applied to the ``spec`` field of the pod template.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-resource-testing
spec:
  title: Resource testing
  description: Play area for testing memory resources
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-resource-testing
  session:
    patches:
      containers:
      - name: workshop
        resources:
          requests:
            memory: "1Gi"
          limits:
            memory: "1Gi"
```

In this example the default memory limit of "512Mi" is increased to "1Gi". Although memory is being set via a patch in this example, the ``session.resources.memory`` field is the preferred way to override the memory allocated to the container the workshop environment is running in.

The patch when applied works a bit differently to overlay patches as found elsewhere in Kubernetes. Specifically, when patching an array and the array contains a list of objects, a search is performed on the destination array and if an object already exists with the same value for the ``name`` field, the item in the source array will be overlaid on top of the existing item in the destination array. If there is no matching item in the destination array, the item in the source array will be added to the end of the destination array.

This means an array doesn't outright replace an existing array, but a more intelligent merge is performed of elements in the array.

Creation of session resources
-----------------------------

When a workshop instance is created, the deployment running the workshop dashboard is created in the namespace for the workshop environment. When more than one workshop instance is created under that workshop environment, all those deployments are in the same namespace.

For each workshop instance, a separate empty namespace is created with name corresponding to the workshop session. The workshop instance is configured so that the service account that the workshop instance runs under can access and create resources in the namespace created for that workshop instance. Each separate workshop instance has its own corresponding namespace and they can't see the namespace for another instance.

If you want to pre-create additional resources within the namespace for a workshop instance, you can supply a list of the resources against the ``session.objects`` field within the workshop definition. You might use this to add additional custom roles to the service account for the workshop instance when working in that namespace, or to deploy a distinct instance of an application for just that workshop instance, such as a private image registry.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-registry-testing
spec:
  title: Registry Testing
  description: Play area for testing image registry
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-registry-testing
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
```

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

For examples of making use of the available parameters see the following sections.

Overriding default RBAC rules
-----------------------------

By default the service account created for the workshop instance, has ``admin`` role access to the session namespace created for that workshop instance. This enables the service account to be used to deploy applications to the session namespace, as well as manage secrets and service accounts.

Where a workshop doesn't require ``admin`` access for the namespace, you can reduce the level of access it has to ``edit`` or ``view`` by setting the ``session.namespaces.role`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-role-testing
spec:
  title: Role Testing
  description: Play area for testing roles
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-role-testing
  session:
    namespaces:
      role: view
```

If you need to add additional roles to the service account, such as the ability to work with custom resource types which have been added to the cluster, you can add the appropriate ``Role`` and ``RoleBinding`` definitions to the ``session.objects`` field described previously.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-kpack-testing
spec:
  title: Kpack Testing
  description: Play area for testing kpack
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-kpack-testing
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
```

Because the subject of a ``RoleBinding`` needs to specify the service account name and namespace it is contained within, both of which are unknown in advance, references to parameters for the workshop namespace and service account for the workshop instance are used when defining the subject.

Adding additional resources via ``session.objects`` can also be used to grant cluster level roles, which would be necessary if you need to grant the service account ``cluster-admin`` role.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-admin-testing
spec:
  title: Admin Testing
  description: Play area for testing cluster admin
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-admin-testing
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
```

In this case the name of the cluster role binding resource embeds ``$(session_namespace)`` so that its name is unique to the workshop instance and doesn't overlap with a binding for a different workshop instance.

Running user containers as root
-------------------------------

In addition to RBAC which controls what resources a user can create and work with, pod security policies are applied to restrict what pods/containers a user deploys can do.

By default the deployments that can be created by a workshop user are only allowed to run containers as a non root user. This means that many container images available on registries such as Docker Hub may not be able to be used.

If you are creating a workshop where a user needs to be able to run containers as the root user, you need to override the default ``nonroot`` security policy and select the ``anyuid`` security policy using the ``session.namespaces.security.policy`` setting.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-policy-testing
spec:
  title: Policy Testing
  description: Play area for testing security policies
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-policy-testing
  session:
    namespaces:
      security:
        policy: anyuid
```

This setting applies to the primary session namespace and any secondary namespaces that may be created.

Creating additional namespaces
------------------------------

For each workshop instance a primary session namespace is created, into which applications can be pre-deployed, or deployed as part of the workshop.

If you need more than one namespace per workshop instance, you can create secondary namespaces in a couple of ways.

If the secondary namespaces are to be created empty, you can list the details of the namespaces under the property ``session.namespaces.secondary``.

```yaml
    apiVersion: training.educates.dev/v1beta1
    kind: Workshop
    metadata:
      name: lab-namespace-testing
    spec:
      title: Namespace Testing
      description: Play area for testing namespaces
      content:
        files: github.com/vmware-tanzu-labs-tests/lab-namespace-testing
      session:
        namespaces:
          role: admin
          budget: medium
          secondary:
          - name: $(session_namespace)-apps
            role: edit
            budget: large
            limits:
              default:
                memory: 512mi
```

When secondary namespaces are created, by default, the role, resource quotas and limit ranges will be set the same as the primary session namespace. Each namespace will though have a separate resource budget, it is not shared.

If required, you can override what ``role``, ``budget`` and ``limits`` should be applied within the entry for the namespace.

Similarly, you can override the security policy for secondary namespaces on a case by case basis by adding the ``security.policy`` setting under the entry for the secondary namespace.

If you also need to create resources in the namespaces you want to create, you may prefer creating the namespaces by adding an appropriate ``Namespace`` resource to ``session.objects``, along with the definitions of the resources you want to create in the namespaces.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-namespace-testing
spec:
  title: Namespace Testing
  description: Play area for testing namespaces
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-namespace-testing
  session:
    objects:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: $(session_namespace)-apps
```

When listing any other resources to be created within the additional namespace, such as deployments, ensure that the ``namespace`` is set in the ``metadata`` of the resource, e.g., ``$(session_namespace)-apps``.

If you need to override what role the service account for the workshop instance has in the additional namespace, you can set the ``training.educates.dev/session.role`` annotation on the ``Namespace`` resource.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-namespace-testing
spec:
  title: Namespace Testing
  description: Play area for testing namespaces
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-namespace-testing
  session:
    objects:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: $(session_namespace)-apps
        annotations:
          training.educates.dev/session.role: view
```

If you need to have a different resource budget set for the additional namespace, you can add the annotation ``training.educates.dev/session.budget`` in the ``Namespace`` resource metadata and set the value to the required resource budget.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-namespace-testing
spec:
  title: Namespace Testing
  description: Play area for testing namespaces
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-namespace-testing
  session:
    objects:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: $(session_namespace)-apps
        annotations:
          training.educates.dev/session.budget: large
```

In order to override the limit range values applied corresponding to the budget applied, you can add annotations starting with ``training.educates.dev/session.limits.`` for each entry.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-namespace-testing
spec:
  title: Namespace Testing
  description: Play area for testing namespaces
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-namespace-testing
  session:
    objects:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: $(session_namespace)-apps
        annotations:
          training.educates.dev/session.limits.min.cpu: 50m
          training.educates.dev/session.limits.min.memory: 32Mi
          training.educates.dev/session.limits.max.cpu: 1
          training.educates.dev/session.limits.max.memory: 1Gi
          training.educates.dev/session.limits.defaultrequest.cpu: 50m
          training.educates.dev/session.limits.defaultrequest.memory: 128Mi
          training.educates.dev/session.limits.request.cpu: 500m
          training.educates.dev/session.limits.request.memory: 1Gi
```

You only need to supply annotations for the values you want to override.

If you need more fine grained control over the limit ranges and resource quotas, set the value of the annotation for the budget to ``custom`` and add the ``LimitRange`` and ``ResourceQuota`` definitions to ``session.objects``.

In this case you must set the ``namespace`` for the ``LimitRange`` and ``ResourceQuota`` resource to the name of the namespace, e.g., ``$(session_namespace)-apps`` so they are only applied to that namespace.

If you need to set the security policy for a specific namespace different to the primary session namespace, you can add the annotation ``training.educates.dev/session.security.policy`` in the ``Namespace`` resource metadata and set the value to ``nonroot`` or ``anyuid`` as necessary.

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
* ``service_account`` - The name of a service account that can be used when creating deployments in the workshop namespace.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.
* ``ingress_secret`` - The name of the ingress secret stored in the workshop namespace when secure ingress is being used.

If you want to create additional namespaces associated with the workshop environment, embed a reference to ``$(workshop_namespace)`` in the name of the additional namespaces, with an appropriate suffix. Be mindful that the suffix doesn't overlap with the range of session IDs for workshop instances.

When creating deployments in the workshop namespace, set the ``serviceAccountName`` of the ``Deployment`` resouce to ``$(service_account)``. This will ensure the deployment makes use of a special pod security policy set up by Educates. If this isn't used and the cluster imposes a more strict default pod security policy, your deployment may not work, especially if any image expects to run as ``root``.

Workshop pod security policy
----------------------------

The pod for the workshop session will be setup with a pod security policy which restricts what can be done from containers in the pod. The nature of the applied pod security policy will be adjusted when enabling support for doing docker builds to enable the ability to do docker builds inside the side car container attached to the workshop container.

If you are customising the workshop by patching the pod specification using ``session.patches``, in order to add your own side car container, and that side car container needs to run as the root user, or needs a custom pod security policy, you will need to override the default security policy for the workshop container.

In the case where you need to allow a side car container to run as the root user and no extra privileges are required, you can override the default ``nonroot`` security policy and set it to ``anyuid``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-policy-testing
spec:
  title: Policy Testing
  description: Play area for testing security policies
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-policy-testing
  session:
    security:
      policy: anyuid
```

Note that this is a different setting than that described previously for changing the security policy for deployments made by a workshop user to the session namespaces. This setting only applies to the workshop container itself.

If you need more fine grained control of the security policy you will need to provide your own resources for defining the pod security policy and map it so it is used. The details of the pod security policy will need to be included in ``environment.objects`` and mapped by definitions added to ``session.objects``. For this to be used, you will need to disable the application of the inbuilt pod security policies. This can be done by setting ``session.security.policy`` to ``custom``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-policy-testing
spec:
  title: Policy Testing
  description: Play area for testing policy override
  content:
    files: github.com/vmware-tanzu-labs-tests/lab-policy-testing
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
        name: aa-$(workshop_namespace)-podman
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
        - aa-$(workshop_namespace)-podman
```

By overriding the pod security policy you are responsible for limiting what can be done from the workshop pod. In other words, you should only add just the extra capabilities you need. The pod security policy will only be applied to the pod the workshop session runs in, it does not affect any pod security policy applied to service accounts which exist in the session namespace or other namespaces which have been created.

Note that due to a lack of a good way to deterministically determine priority of applied pod security policies when a default pod security policy has been applied globally by mapping it to the ``system:authenticated`` group, with priority instead falling back to ordering of the names of the pod security policies, it is recommend you use ``aa-`` as a prefix to the custom pod security name you create. This will ensure that it take precedence over any global default pod security policy such as ``restricted``, ``pks-restricted`` or ``vmware-system-tmc-restricted``, no matter what the name of the global policy default is called.

(defining-additional-ingress-points)=
Defining additional ingress points
----------------------------------

If running additional background applications, by default they are only accessible to other processes within the same container. In order for an application to be accessible to a user via their web browser, an ingress needs to be created mapping to the port for the application.

You can do this by supplying a list of the ingress points, and the internal container port they map to, by setting the ``session.ingresses`` field in the workshop definition.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    ingresses:
    - name: application
      port: 8080
```

The form of the hostname used in URL to access the service will be:

```text
application-$(session_namespace).$(ingress_domain)
```

Note that it is also possible to specify ``-application`` as a suffix in the first component of the full host name. This was an older convention and is still supported, however the ``application-`` prefix is preferred as it would allow a workshop to be deployed standalone using ``docker`` independent of Educates, with access using a ``nip.io`` style address.

You should not use as the name, the name of any builtin dashboards, ``terminal``, ``console``, ``slides`` or ``editor``. These are reserved for the corresponding builtin capabilities providing those features.

In addition to specifying ingresses for proxying to internal ports within the same pod, you can specify a ``host``, ``protocol`` and ``port`` corresponding to a separate service running in the Kubernetes cluster.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    ingresses:
    - name: application
      protocol: http
      host: service.namespace.svc.cluster.local
      port: 8080
```

Variables providing information about the current session can be used within the ``host`` property if required.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    ingresses:
    - name: application
      protocol: http
      host: service.$(session_namespace).svc.cluster.local
      port: 8080
```

The available variables are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.

If the service uses standard ``http`` or ``https`` ports, you can leave out the ``port`` property and the port will be set based on the value of ``protocol``.

When a request is being proxied, you can specify additional request headers that should be passed to the service.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    ingresses:
    - name: application
      protocol: http
      host: service.$(session_namespace).svc.cluster.local
      port: 8080
      headers:
      - name: Authorization
        value: "Bearer $(kubernetes_token)"
```

The value of a header can reference the following variables.

* ``kubernetes_token`` - The access token of the service account for the current workshop session, used for accessing the Kubernetes REST API.

Accessing any service via the ingress will be protected by any access controls enforced by the workshop environment or training portal. If the training portal is used this should be transparent, otherwise you will need to supply any login credentials for the workshop again when prompted by your web browser.

If you want to disable the access controls you can override the authentication type for the ingress. The default for ``authentication.type`` is ``session``. To disable, set this to ``none``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    ingresses:
    - name: application
      authentication:
        type: none
      protocol: http
      host: service.namespace.svc.cluster.local
      port: 8080
```

If required, the downstream service can implement its own authentication, such as HTTP basic authentication.

External workshop instructions
------------------------------

In place of using workshop instructions provided with the workshop content, you can use externally hosted instructions instead. To do this set ``sessions.applications.workshop.url`` to the URL of an external web site.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      workshop:
        url: https://www.example.com/instructions
```

The external web site must be able to displayed in an HTML iframe, will be shown as is and should provide its own page navigation and table of contents if required.

The URL value can reference a number of pre-defined parameters. The available parameters are:

* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

These could be used for example to reference workshops instructions hosted as part of the workshop environment.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      workshop:
        url: $(ingress_protocol)://$(workshop_namespace)-instructions.$(ingress_domain)
  environment:
    objects:
    - ...
```

In this case ``environment.objects`` of the workshop ``spec`` would need to include resources to deploy the application hosting the instructions and expose it via an appropriate ingress.

Disabling workshop instructions
-------------------------------

The aim of the workshop environment is to provide instructions for a workshop which users can follow. If you want instead to use the workshop environment as a development environment, or use it as an admistration console which provides access to a Kubernetes cluster, you can disable the display of workshop instructions provided with the workshop content. In this case only the workarea with the terminals, console etc, will be displayed. To disable display of workshop instructions, add a ``session.applications.workshop`` section and set the ``enabled`` property to ``false``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      workshop:
        enabled: false
```

Enabling the Kubernetes console
-------------------------------

By default the Kubernetes console is not enabled. If you want to enable it and make it available through the web browser when accessing a workshop, you need to add a ``session.applications.console`` section to the workshop definition, and set the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      console:
        enabled: true
```

The Kubernetes dashboard provided by the Kubernetes project will be used. If you would rather use Octant as the console, you can set the ``vendor`` property to ``octant``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      console:
        enabled: true
        vendor: octant
```

When ``vendor`` is not set, ``kubernetes`` is assumed.

Enabling the integrated editor
------------------------------

By default the integrated web based editor is not enabled. If you want to enable it and make it available through the web browser when accessing a workshop, you need to add a ``session.applications.editor`` section to the workshop definition, and set the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      editor:
        enabled: true
```

The integrated editor which is used is based on VS Code. Details of the editor can be found at:

* [https://github.com/cdr/code-server](https://github.com/cdr/code-server)

If you need to install additional VS Code extensions, this can be done from the editor. Alternatively, if building a custom workshop, you can install them from your ``Dockerfile`` into your workshop image by running:

```text
code-server --install-extension vendor.extension
```

Replace ``vendor.extension`` with the name of the extension, where the name identifies the extension on the VS Code extensions marketplace used by the editor, or provide a path name to a local ``.vsix`` file.

This will install the extensions into ``$HOME/.config/code-server/extensions``.

If downloading extensions yourself and unpacking them, or you have them as part of your Git repository, you can instead locate them in the ``workshop/code-server/extensions`` directory.

Enabling workshop downloads
---------------------------

At times you may want to provide a way for a workshop user to download files which are provided as part of the workshop content. This capability can be enabled by adding the ``session.applications.files`` section to the workshop definition, and setting the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      files:
        enabled: true
```

The recommended way of providing access to files from workshop instructions is using the ``files:download-file`` clickable action block. This action will ensure any file is downloaded to the local machine and not simply displayed in the browser in place of the workshop instructions.

By default any files located under the home directory of the workshop user account can be accessed. To restrict where files can be download from, set the ``directory`` setting.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      files:
        enabled: true
        directory: exercises
```

When the specified directory is a relative path, it is evaluated relative to the home directory of the workshop user.

Enabling the test examiner
--------------------------

The test examiner is a feature which allows a workshop to have verification checks which can be triggered from the workshop instructions. The test examiner is disabled by default. If you want to enable it, you need to add a ``session.applications.examiner`` section to the workshop definition, and set the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      examiner:
        enabled: true
```

Any executable test programs to be used for verification checks need to be provided in the ``workshop/examiner/tests`` directory.

The test programs should return an exit status of 0 if the test is successful and non zero if a failure. The test programs should not be persistent programs that would run forever.

Clickable actions for the test examiner are used within the workshop instructions to trigger the verification checks, or they can be configured to be automatically started when the page of the workshop instructions is loaded.

Enabling session image registry
-------------------------------

Workshops using tools such as ``kpack`` or ``tekton`` and which need a place to push container images when built, can enable an image registry. A separate image registry is deployed for each workshop session.

Note that the image registry is only currently fully usable if workshops are deployed under an Educates operator configuration which uses secure ingress. This is because an insecure registry would not be trusted by the Kubernetes cluster as the source of container images when doing deployments.

To enable the deployment of an image registry per workshop session you need to add a ``session.applications.registry`` section to the workshop definition, and set the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      registry:
        enabled: true
```

The image registry will mount a persistent volume for storing of images. By default the size of that persistent volume is 5Gi. If you need to override the size of the persistent volume add the ``storage`` property under the ``registry`` section.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      registry:
        enabled: true
        storage: 20Gi
```

The amount of memory provided to the image registry will default to 768Mi. If you need to increase this, add the ``memory`` property under the ``registry`` section.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      registry:
        enabled: true
        memory: 1Gi
```

The image registry will be secured with a username and password unique to the workshop session and expects access over a secure connection.

To allow access from the workshop session, the file ``$HOME/.docker/config.json`` containing the registry credentials will be injected into the workshop session. This will be automatically used by tools such as ``docker``.

For deployments in Kubernetes, a secret of type ``kubernetes.io/dockerconfigjson`` is created in the namespace and automatically applied to the ``default`` service account in the namespace. This means deployments made using the default service account will be able to pull images from the image registry without additional configuration. If creating deployments using other service accounts, you will need to add configuration to the service account or deployment to add the registry secret for pulling images.

If you need access to the raw registry host details and credentials, they are provided as environment variables in the workshop session. The environment variables are:

* ``REGISTRY_HOST`` - Contains the host name for the image registry for the workshop session.
* ``REGISTRY_AUTH_FILE`` - Contains the location of the ``docker`` configuration file. Should always be the equivalent of ``$HOME/.docker/config.json``.
* ``REGISTRY_USERNAME`` - Contains the username for accessing the image registry.
* ``REGISTRY_PASSWORD`` - Contains the password for accessing the image registry. This will be different for each workshop session.
* ``REGISTRY_SECRET`` - Contains the name of a Kubernetes secret of type ``kubernetes.io/dockerconfigjson`` added to the session namespace and which contains the registry credentials.

The URL for accessing the image registry adopts the HTTP protocol scheme inherited from the environment variable ``INGRESS_PROTOCOL``. This would be the same HTTP protocol scheme as the workshop sessions themselves use.

If you want to use any of the variables as data variables in workshop content, use the same variable name but in lower case. Thus, ``registry_host``, ``registry_auth_file``, ``registry_username``, ``registry_password`` and ``registry_secret``.

Enabling ability to use docker
------------------------------

If you need to be able to build container images in a workshop using ``docker``, it needs to be enabled first. Each workshop session will be provided with its own separate docker daemon instance running in a container.

Note that enabling of support for running ``docker`` requires the use of a privileged container for running the docker daemon. Because of the security implications of providing access to docker with this configuration, it is strongly recommended that if you don't trust the people doing the workshop, any workshops which require docker only be hosted in a disposable Kubernetes cluster which is destroyed at the completion of the workshop. You should never enable docker for workshops hosted on a public service which is always kept running and where arbitrary users could access the workshops.

To enable support for being able to use ``docker`` add a ``session.applications.docker`` section to the workshop definition, and set the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      docker:
        enabled: true
```

The container which runs the docker daemon will mount a persistent volume for storing of images which are pulled down or built locally. By default the size of that persistent volume is 5Gi. If you need to override the size of the persistent volume add the ``storage`` property under the ``docker`` section.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      docker:
        enabled: true
        storage: 20Gi
```

The amount of memory provided to the container running the docker daemon will default to 768Mi. If you need to increase this, add the ``memory`` property under the ``registry`` section.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      docker:
        enabled: true
        memory: 1Gi
```

Access to the docker daemon from the workshop session uses a local UNIX socket shared with the container running the docker daemon. If using a local tool which wants to access the socket connection for the docker daemon directly rather than by running ``docker``, it should use the ``DOCKER_HOST`` environment variable to determine the location of the socket.

The docker daemon is only available from within the workshop session and cannot be accessed outside of the pod by any tools deployed separately to Kubernetes.

Enabling WebDAV access to files
-------------------------------

Local files within the workshop session can be accessed or updated from the terminal command line or editor of the workshop dashboard. The local files reside in the filesystem of the container the workshop session is running in.

If there is a need to be able to access the files remotely, it is possible to enable WebDAV support for the workshop session.

To enable support for being able to access files over WebDAV add a ``session.applications.webdav`` section to the workshop definition, and set the ``enabled`` property to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      webdav:
        enabled: true
```

The result of this will be that a WebDAV server will be run within the workshop session environment. A set of credentials will also be automatically generated which are available as environment variables. The environment variables are:

* ``WEBDAV_USERNAME`` - Contains the username which needs to be used when authenticating over WebDAV.
* ``WEBDAV_PASSWORD`` - Contains the password which needs to be used authenticating over WebDAV.

If you need to use any of the environment variables related to the image registry as data variables in workshop content, you will need to declare this in the ``workshop/modules.yaml`` file in the ``config.vars`` section.

```yaml
config:
  vars:
  - name: WEBDAV_USERNAME
  - name: WEBDAV_PASSWORD
```

The URL endpoint for accessing the WebDAV server is the same as the workshop session, with ``/webdav/`` path added. This can be constructed from the terminal using:

```text
$INGRESS_PROTOCOL://$SESSION_NAMESPACE.$INGRESS_DOMAIN/webdav/
```

In workshop content it can be constructed using:

```text
{{ingress_protocol}}://{{session_namespace}}.{{ingress_domain}}/webdav/
```

You should be able to use WebDAV client support provided by your operating system, of by using a standalone WebDAV client such as [CyberDuck](https://cyberduck.io/).

Using WebDAV can make it easier if you need to transfer files to or from the workshop session.

Customizing the terminal layout
-------------------------------

By default a single terminal is provided in the web browser when accessing the workshop. If required, you can enable alternate layouts which provide additional terminals. To set the layout, you need to add the ``session.applications.terminal`` section and include the ``layout`` property with the desired layout.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    applications:
      terminal:
        enabled: true
        layout: split
```

The options for the ``layout`` property are:

* ``default`` - Single terminal.
* ``split`` - Two terminals stacked above each other in ratio 60/40.
* ``split/2`` - Three terminals stacked above each other in ratio 50/25/25.
* ``lower`` - A single terminal is placed below any dashboard tabs, rather than being a tab of its own. The ratio of dashboard tab to terminal is 70/30.
* ``none`` - No terminal is displayed, but they can still be created from the drop down menu.

When adding the ``terminal`` section, you must include the ``enabled`` property and set it to ``true`` as it is a required field when including the section.

If you didn't want a terminal displayed, and also wanted to disable the ability to create terminals from the drop down menu, set ``enabled`` to ``false``.

Adding custom dashboard tabs
----------------------------

Exposed applications, external sites and additional terminals, can be given their own custom dashboard tab. This is done by specifying the list of dashboard panels and the target URL.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    ingresses:
    - name: application
      port: 8080
    dashboards:
    - name: Internal
      url: "$(ingress_protocol)://application-$(session_namespace).$(ingress_domain)/"
    - name: External
      url: http://www.example.com
```

The URL values can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The URL can reference an external web site if required. Do note however, that any web site must not prohibit being embedded in a HTML iframe. Further, if Educates is configured to use secure ingress, the site being embedded in the dashboard cannot use HTTP and must also use a secure HTTPS URL otherwise the browser will prohibit accessing the embedded site due to mixed content.

In the case of wanting to have a custom dashboard tab provide an additional terminal, the ``url`` property should use the form ``terminal:<session>``, where ``<session>`` is replaced with the name of the terminal session. The name of the terminal session can be any name you choose, but should be restricted to lower case letters, numbers and '-'. You should avoid using numeric terminal session names such as "1", "2" and "3" as these are use for the default terminal sessions.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-application-testing
spec:
  title: Application Testing
  description: Play area for testing my application
  content:
    image: ghcr.io/vmware-tanzu-labs/lab-application-testing:master
  session:
    dashboards:
    - name: Example
      url: terminal:example
```
