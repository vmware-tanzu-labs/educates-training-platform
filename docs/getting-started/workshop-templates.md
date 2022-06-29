(workshop-templates)=
Workshop Templates
==================

The Educates workshop templates provide a starting point for creating your workshops. The templates are tailored for working with the local Educates environment, but can be customized to suit any deployment of Educates.

When creating a new workshop it is possible to provide options to the workshop creation script to customize the workshop details, as well as add in pre-canned functionality supporting a range of use cases.

Customizing workshop details
----------------------------

To create a new workshop using the creation script provided with the Educates workshop templates you would run:

```
educates-workshop-templates/create-workshop.sh lab-new-workshop
```

The argument is the name for the workshop. The name of the workshop must conform to what is valid for a RFC 1035 label name as detailed in [Kubernetes object name and ID](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/) requirements, but instead of a maximum length of 63 characters it is recommended the name be no longer than 25 characters. The shorter length requirement is due to Educates needing to add prefixes or suffixes as part of the implementation in different circumstances.

As well as the name supplied being used for the name of the directory created, it is also used as the name for the Educates `Workshop` resource definition, and sample `TrainingPortal` resource definition.

In the workshop definition there are additional required fields that need to be filled out. These will be filled out with default values, but you can customize them at the time of workshop creation.

The fields which can be customized are:

* `workshop.title` - A short title describing the workshop.
* `workshop.description` - A longer description of the workshop.
* `workshop.image` - The name of an alternate workshop base image to use for the workshop. Options for workshop base images supplied with Educates are `jdk8-environment:*`, `jdk11-environment:*`, `jdk17-environment:*` and `conda-environment:*`.

The fields can be supplied when creating a new workshop using the `--data-value` option.

```
educates-workshop-templates/create-workshop.sh lab-new-workshop \
  --data-value workshop.title="New Workshop" \
  --data-value workshop.description="New workshop using Educates"
```

Workshop files containing user instructions for the workshop by default use Markdown. If you instead want to use ASCIIDoc, supply the `--text-format asciidoc` option.

```
educates-workshop-templates/create-workshop.sh lab-new-workshop --text-format asciidoc
```

Adding workshop overlays
------------------------

The default workshop template provides a minimal configuration for a basic workshop environment. To assist in creating workshops for more complicated use cases, a set of overlays can be applied which will customize the workshop configuration for specific tasks. The currently available overlays are:

* `spring-initialzr` - Adds configuration to embed an instance of the `start.spring.io` site into a workshop session dashboard, but where generated application code is unpacked into the workshop session container instead of being downloaded to the local machine.
* `virtual-cluster` - Adds configuration to create a Kubernetes virtual cluster per workshop session. A workshop user has cluster admin access to the virtual cluster, ``kapp-controller`` is pre-installed into the virtual cluster, and `kctrl` command is provided.

To apply an overlay use the ``--overlay`` option. The option can be used more than once.

```
educates-workshop-templates/create-workshop.sh lab-new-workshop --overlay virtual-cluster
```

Note that the various overlays are still experimental and it is forseen that how they work will change as Educates is modified to better support specialised use cases. Some capabilities offered through the overlays may in time be integrated into Educates as a core feature. It is highly recommended to always reach out to the Educates team before using them so as to understand their current state, how to use them, and any limitations.

Custom workshop base image
--------------------------

The default workshop template uses an OCI image artefact to package up the workshop content files. This is overlayed on top of the standard base workshop image, or one of the alternatives provided with Educates. A typical configuration for this which would be found in the `resources/workshop.yaml` file would be:

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

If you want to create your own custom workshop base image a `Dockerfile` is supplied which you can use as a starting point for creating it. To have the custom workshop base image be used, you need to modify the workshop definition. Specifically, you need to add `spec.workshop.image` property as follows:

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

In both examples above, the value of `{name}` would be the name of your workshop. That is, the same as `metadata.name` from the same resource definition.

The values for `image` and `files.image.url`, with reference to the data variable `$(image_repository)`, will ensure that the respective custom workshop base image and OCI artefact containing the workshop content files are pulled from the image registry created with the local Kubernetes environment. That is, you do not need to provide an explicit name for the image registry host as Educates will substitute the appropriate value.

To build the custom workshop base image you can run `make` as:

```
make build-image
```

or to both build and publish the image, run:

```
make publish-image
```

So that running `make` with no arguments the first time building the workshop for working on it locally, also builds the image, modify the `Makefile` and change the `all` target to:

```
all: publish-files publish-image deploy-workshop
```

Hosting workshops on GitHub
---------------------------

The workshop template will add to a new workshop a GitHub actions workflow to assist in automatically publishing tagged versions of workshops as releases to GitHub.

If using GitHub to host your workshop content, and you are ready to make it available for others to use, use `git` to create a version tag against the commit for the stable version, where the format of the tag is `X.Y`, e.g., `1.0`. Push the tag to GitHub.

The tag being pushed to GitHub will trigger the following actions:

* If an OCI image artefact is being used for workshop content files, it will be built and pushed to GitHub container registry with the specified tag.
* If a custom workshop base image is being used, it will be built and pushed to GitHub container registry with the specified tag.
* A GitHub release will be created linked to the specified tag.
* The `resources/workshop.yaml` file with the workshop resource definition will be attached to the release with name ``workshops.yaml``. The `image` and `files.image.url` references in the workshop definition will be rewritten to use the images from GitHub container registry.
* The `resources/trainingportal.yaml` file with the sample training portal resource definition will be attached to the release with the name ``trainingportal.yaml``.

Note that if the GitHub repository is not public, you will need to go to the settings for any images pushed to GitHub container registry and change the visibility from private or internal, to public before anyone can use the workshop.

To use the workshop, the workshop and training portal definitions can be applied to a Kubernetes cluster directly from the GitHub release. For example:

```
kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/4.1/workshops.yaml
kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/4.1/trainingportal.yaml
```

The automatic rewriting of the `image` and `files.image.url` references in the workshop definition to use the images published to GitHub container registry relies on the values for those fields being those which are setup by the workshop template to use the image registry deployed with the local Kubernetes environment. That is of the form:

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

If you have changed these because you were not using the local Educates environment to develop your workshop content, you will need to configure the GitHub action workflow to tell it what to expect for these values so it knows what to rewrite.

See the more detailed [documentation](https://github.com/vmware-tanzu-labs/educates-github-actions/blob/main/publish-workshop/README.md) about the GitHub action used to publish the workshop on how to configure it.

Going forward it will be expected that any workshops to be published to Tanzu Developer Center are hosted on GitHub under the `vmware-tanzu-labs` organization and make use of this GitHub action to release tagged versions of workshops.
