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

* `workshop.title`: A short title describing the workshop.
* `workshop.description`: A longer description of the workshop.
* `workshop.image`: The name of an alternate workshop base image to use for the workshop. Options for workshop base images supplied with Educates are `jdk8-environment:*`, `jdk11-environment:*` and `conda-environment:*`.

* `registry.host`: The host name of the registry where workshop files or images will be stored. Defaults to `registry.eduk8s.svc.cluster.local:5001`, the image registry created with the local Educates environment.
* `registry.namespace`: The organization or account namespace on the registry where workshop files or images will be stored. Defaults to being unset.
* `registry.protocol`: The protocol used for the registry when pulling down workshop files as OCI artefacts from the registry. Defaults to `http`.

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

Hosting workshops on GitHub
---------------------------
