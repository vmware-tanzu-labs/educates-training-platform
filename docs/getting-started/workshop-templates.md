(workshop-templates)=
Workshop Templates
==================

The Educates workshop template provides a starting point for creating your workshops. The template is tailored for working with the local Educates environment, but can be customized to suit any deployment of Educates. When creating a new workshop it is possible to provide options to customize the workshop details.

Customizing workshop details
----------------------------

To create a new workshop using the Educates command line tool you would run the `educates new-workshop` command, passing it as argument a directory path to where the workshop content should be placed.

```
educates new-workshop lab-new-workshop
```

The last component of the supplied path will be used as the workshop name. The name of the workshop must conform to what is valid for a RFC 1035 label name as detailed in [Kubernetes object name and ID](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/) requirements, but instead of a maximum length of 63 characters it is recommended the name be no longer than 25 characters. The shorter length requirement is due to Educates needing to add prefixes or suffixes as part of the implementation in different circumstances.

The ``educates new-workshop`` command will default to create files setup for using the ``classic`` renderer. If you want to use the ``hugo`` renderer use:

```
educates new-workshop lab-new-workshop --template hugo
```

In the workshop definition there are additional required fields that need to be filled out. These will be filled out with default values, but you can customize them at the time of workshop creation.

The command line options for customizing the fields and their purpose are:

* `--title` - A short title describing the workshop.
* `--description` - A longer description of the workshop.
* `--image` - The name of an alternate workshop base image to use for the workshop. Options for workshop base images supplied with Educates are `jdk8-environment:*`, `jdk11-environment:*`, `jdk17-environment:*` and `conda-environment:*`.

Custom workshop base image
--------------------------

The default workshop template uses an OCI image artifact to package up the workshop content files. This is overlayed on top of the standard base workshop image, or one of the alternatives provided with Educates. A typical configuration for this which would be found in the `resources/workshop.yaml` file would be:

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

In the example above, the value of `{name}` would be the name of your workshop. That is, the same as `metadata.name` from the same resource definition.

In the value for `files.image.url`, the reference to the data variable `$(image_repository)` will ensure that the OCI image artifact containing the workshop content files are pulled from the image registry created with the local Kubernetes environment. That is, you do not need to provide an explicit name for the image registry host as Educates will substitute the appropriate value.

If you want to use your own custom workshop image, the location of the image can be supplied using the `--image` option when using the `educates new-workshop` command to create the initial workshop content. This would result in the generated configuration found in `resources/workshop.yaml` including the extra `spec.workshop.image` property.

```yaml
spec:
  workshop:
    image: custom-environment:latest
    files:
    - image:
        url: $(image_repository)/{name}-files:latest
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

If the custom workshop image is specific to the workshop and is not being built and published separately, you can add a `Dockerfile` for creating the custom workshop image to the workshop files. To also use the local image registry for it, you would then set the `spec.workshop.image` property as follows:

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

To build the custom workshop base image and push it to the local registry you would run:

```
docker build -t localhost:5001/{name}-image:latest .
```

The custom workshop base image would then be pulled down from the local image registry for each workshop session.

Note that although it is possible to create custom workshop images, it is recommended that it be avoided if possible. If you need to add additional applications to a workshop session use extension packages instead. By overlaying additional files onto one of the standard workshop base images at the time a workshop is created, rather than creating a custom workshop image, you ensure you are always using the appropriate version of the workshop base image for the version of Educates being used. Using a custom workshop image that is based on an older version of the workshop base images is not guaranteed to always work.

Hosting workshops on GitHub
---------------------------

If hosting workshops on GitHub, the Educates project provides a GitHub action to assist in automatically publishing tagged versions of workshops as releases to GitHub. To make use of the GitHub action, add to your Git repository the file `.github/workflows/publish-workshop.yaml` containing:

```
name: Publish Workshop

on:
  push:
    tags:
      - "[0-9]+.[0-9]+"
      - "[0-9]+.[0-9]+-alpha.[0-9]+"
      - "[0-9]+.[0-9]+-beta.[0-9]+"
      - "[0-9]+.[0-9]+-rc.[0-9]+"

jobs:
  publish-workshop:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Create release
        uses: vmware-tanzu-labs/educates-github-actions/publish-workshop@v5
        with:
          token: ${{secrets.GITHUB_TOKEN}}
```

With the GitHub workflow added, when you are ready to make your workshop available for others to use, use `git` to create a version tag against the commit for the stable version, where the format of the tag is `X.Y`, e.g., `1.0`. Push the tag to GitHub.

The tag being pushed to GitHub will trigger the following actions:

* If an OCI image artifact is being used for workshop content files, it will be built and pushed to GitHub container registry with the specified tag.
* If a custom workshop base image is being used, it will be built and pushed to GitHub container registry with the specified tag.
* A GitHub release will be created linked to the specified tag.
* The `resources/workshop.yaml` file with the workshop resource definition will be attached to the release with name ``workshop.yaml``. The `image` and `files.image.url` references in the workshop definition will be rewritten to use the images from GitHub container registry.

Note that if the GitHub repository is not public, you will need to go to the settings for any images pushed to GitHub container registry and change the visibility from private or internal, to public before anyone can use the workshop.

To use the workshop, you can explicitly load the workshop definition using the `workshop.yaml` file attached to the GitHub release, and then add it to an appropriate training portal, or you could use the Educates command line and run `educates deploy-workshop` supplying the URL for the `workshop.yaml` file attached to the GitHub release: 

```
educates deploy-workshop -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml
```

The automatic rewriting of the `image` and `files.image.url` references in the workshop definition to use the images published to GitHub container registry relies on the values for those fields being as follows:

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

If you have changed these because you were not using the local Educates environment to develop your workshop content, you may be able to configure the GitHub action workflow to tell it what to expect for these values so it knows what to rewrite.

See the more detailed [documentation](https://github.com/vmware-tanzu-labs/educates-github-actions/blob/main/publish-workshop/README.md) about the GitHub action used to publish the workshop on how to configure it.
