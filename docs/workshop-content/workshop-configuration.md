Workshop Configuration
======================

There are two main components to a workshop. The first is the workshop definition, which defines the setup requirements for deploying the workshop and how to configure the Educates environment for that workshop. The second is the workshop files, consisting of the workshop instructions, setup files for the workshop, and any exercise files required for the workshop.

Workshop setup requirements
---------------------------

Workshop images can be deployed directly to a container runtime. To manage deployments into a Kubernetes cluster, the Educates operator is provided. Configuration for the Educates operator is defined by a ``Workshop`` custom resource definition. When using the workshop template to create the initial files for a workshop, this definition is found in the ``resources/workshop.yaml`` file.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  workshop:
    files:
    - git:
        url: https://github.com/vmware-tanzu-labs/lab-markdown-sample
        ref: origin/main
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
  session:
    namespaces:
      budget: small
    applications:
      console:
        enabled: true
      editor:
        enabled: true
```

In this sample workshop files are downloaded from a Git repository hosted on GitHub. This is specified in the ``workshop.files`` section of the workshop definition. The workshop files will be overlaid on top of the standard workshop base image.

As well as the standard workshop base image, Educates also provides workshop base images for working with Java and Python. To select the workshop base image with Java JDK 17 support you would use:

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  workshop:
    image: jdk17-environment:*
    files:
    - git:
        url: https://github.com/vmware-tanzu-labs/lab-markdown-sample
        ref: origin/main
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
  session:
    namespaces:
      budget: small
    applications:
      console:
        enabled: true
      editor:
        enabled: true
```

In this case the alternate workshop image was specified by setting the ``workshop.image`` property.

As well as selecting one of the alternate workshop base images provided by Educates, you could also nominate a custom workshop image of your own:

```yaml
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-markdown-sample
spec:
  title: Markdown Sample
  description: A sample workshop using Markdown
  workshop:
    image: ghcr.io/vmware-tanzu-labs/lab-markdown-sample:latest
  session:
    namespaces:
      budget: small
    applications:
      console:
        enabled: true
      editor:
        enabled: true
```

When using a custom workshop image it can include the workshop files, or you can still download them separately and overlay them on top.

As well as being used to specify the workshop base image to use and the source of any workshop files, the ``Workshop`` definition is used to configure the workshop environment and workshop session. This includes details such as whether the embedded editor or Kubernetes web console is enabled, but also details such as additional resources to deploy with a workshop environment or session, what memory and storage requirements a workshop session has, or what quota is available when deploying workloads into the Kubernetes cluster.

For more details see the separate documentation on the [Workshop definition](workshop-definition).

Instructions rendering options
------------------------------

Educates currently supports two different renderers for workshop instructions.

The first and original renderer for workshop instructions included in Educates is called the ``classic`` renderer. This is a custom dynamic web application for rendering the workshop instructions. It supports the use of Markdown or AsciiDoc.

The second renderer for workshop instructions is the ``hugo`` renderer. As the name suggests this makes use of Hugo to generate workshop instructions as static HTML files, using custom layouts provided by Educates. Hugo only supports the use of Markdown.

In both cases, the pages making up the workshop instructions are placed in the ``workshop/content`` directory. When configuration is needed to specify the navigation path through the workshop instructions, how it is done differs based on the renderer used.

Classic renderer configuration
------------------------------

When using the ``classic`` renderer for workshop instructions, there are multiple ways you can setup the configuration of a workshop to specify the structure of the content. The way used in the sample workshops is through YAML files.

The ``workshop/modules.yaml`` file provides details on the list of available modules which make up your workshop, and data variables for use in content.

In the case of the list of modules, not all modules may end up being used. This is because this list represents the full set of modules you have available and might use. You may want to run variations of your workshop, such as for different programming languages. As such, which modules are active and will be used for a specific workshop are listed in the separate ``workshop/workshop.yaml`` file, along with the name to be given to the workshop when using that set of modules.

By default the ``workshop.yaml`` file will be used to drive what modules are used. Where you want to deliver different variations of the workshop content, you can provide multiple workshop files with different names. You might for example instead provide ``workshop-java.yaml`` and ``workshop-python.yaml``.

Where you have multiple workshop files, and don't have the default ``workshop.yaml`` file, you can specify the workshop file to use by setting the ``WORKSHOP_FILE`` environment variable in the runtime configuration for the workshop.

The format for listing the available modules in the ``workshop/modules.yaml`` file is:

```yaml
modules:
  00-workshop-overview:
    name: Workshop Overview
    exit_sign: Start Workshop
  01-workshop-instructions:
    name: Workshop Instructions
  99-workshop-summary:
    name: Workshop Summary
    exit_sign: Finish Workshop
```

Each available module is listed under ``modules``, where the name used corresponds to the path to the file containing the content for that module, with any extension identifying the content type left off.

For each module, set the ``name`` field to the page title to be displayed for that module. If no fields are provided and ``name`` is not set, the title for the module will be calculated from the name of the module file.

The corresponding ``workshop/workshop.yaml`` file, where all available modules were being used, would have the format:

```yaml
name: Workshop

modules:
  activate:
  - 00-workshop-overview
  - 01-workshop-instructions
  - 99-workshop-summary
```

The top level ``name`` field in this file is the name for this variation of the workshop content.

The ``modules.activate`` field is a list of modules to be used for the workshop. The names in this list must match the names as they appear in the modules file.

The order in which pages are traversed, is dictated by the order in which modules are listed under the ``modules.activate`` field in the workshop configuration file. The order in which modules appear in the modules configuration file is not relevant.

At the bottom of each page a "Continue" button will be displayed to go to the next page in sequence. The label on this button can be customised by setting the ``exit_sign`` field in the entry for the module in the modules configuration file.

For the last module in the workshop, a button will still be displayed, but where the user is taken when the button is pressed can vary.

If you want the user to be taken to a different web site upon completion you can set the ``exit_link`` field of the final module to an external URL. Alternatively, the ``RESTART_URL`` environment variable can be set from a workshop environment to control where the user is taken.

If a destination for the final page is not provided the user will be redirected back to the starting page of the workshop.

When using the training portal, it will override this environment variable so that at the completion of a workshop the user is directed back to the training portal.

The recommendation is that for the last page the ``exit_sign`` be set to "Finish Workshop" and ``exit_link`` not be specified. This will enable the destination to be controlled from the workshop environment or training portal.

(hugo-renderer-configuration)=
Hugo renderer configuration
---------------------------

When using the ``hugo`` renderer for workshop instructions, the need to specify explicitly via a separate configuration file the navigation path through the instructions is optional.

By default when using the ``hugo`` renderer, all pages will be included within the navigation path of the workshop instructions. The order in which pages are included will be calculated based on the pathname of the pages within the ``workshop/content`` directory. If you would prefer instead to use Hugo's default page ordering mechanism, you can add page weight fields in the metadata of each page to dictate ordering. In that case the ordering will be based on page weight followed by page title. To specify the title for a page, you can add a title field in the metadata of each page.

If you would prefer to specify the order of pages via a YAML file, only have certain pages included, or have the option of multiple pathways which can be selected, a ``workshop/config.yaml`` file can be provided which defines this information.

If you elect to use the ``workshop/config.yaml``, the structure it would contain where using it to define the navigation pathways would be as follows:

```yaml
pathways:
  default: workshop

  paths:
    workshop:
      title: "Workshop"

      steps:
      - 00-workshop-overview
      - 01-workshop-instructions
      - 99-workshop-summary

modules:
- name: 00-workshop-overview
  title: Workshop Overview
- name: 01-workshop-instructions
  title: Workshop Instructions
- name: 99-workshop-summary
  title: Workshop Summary
```

Unlike with the ``classic`` render, the ``modules`` section is optional even when specifying the navigation pathway. When a module which is part of a pathway is being rendered, without an entry in ``modules`` it will use any page title defined in the metadata of the page itself.

If you want multiple possible pathways, you can list the steps for each in separate sections under ``pathways.paths``. The ``pathways.default`` value should specify the default pathway. You can override the workshop title in the ``title`` field of a specific pathway.

To select which pathway is used when the workshop is started, you can set the ``PATHWAY_NAME`` environment variable in the workshop definition to the name of the pathway.

When using the ``hugo`` renderer, there is no way to override navigation button labels or where clicking on them will direct you as was possible with the ``classic`` renderer.
