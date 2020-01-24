Workshop Config
===============

There are two main parts to the configuration for a workshop. The first specifies the structure of the workshop content and the second defines the runtime requirements for deploying the workshop.

Specifying structure of the content
-----------------------------------

There are multiple ways you can setup configuration for a workshop. The way used in the sample workshops is through YAML files.

The ``workshop/modules.yaml`` file provides details on the list of available modules which make up your workshop, and data variables for use in content.

In the case of the list of modules, not all modules may end up being used. This is because this list represents the full set of modules you have available and might use. You may want to run variations of your workshop, such as for different programming languages. As such, which modules are active and will be used for a specific workshop are listed in the separate ``workshop/workshop.yaml`` file, along with the name to be given to the workshop when using that set of modules.

By default the ``workshop.yaml`` file will be used to drive what modules are used. Where you want to deliver different variations of the workshop content, you can provide multiple workshop files with different names. You might for example instead provide ``workshop-java.yaml`` and ``workshop-python.yaml``.

Where you have multiple workshop files, and don't have the default ``workshop.yaml`` file, you can specify the default workshop file to use by setting the ``WORKSHOP_FILE`` environment variable in the runtime configuration for the workshop.

The format for listing the available modules in the ``workshop/modules.yaml`` file is:

.. code-block:: yaml

    modules:
        workshop-overview:
            name: Workshop Overview
            exit_sign: Setup Environment
        setup-environment:
            name: Setup Environment
            exit_sign: Start Workshop
        exercises/01-sample-content:
            name: Sample Content
        workshop-summary:
            name: Workshop Summary
            exit_sign: Finish Workshop

Each available module is listed under ``modules``, where the name used corresponds to the path to the file containing the content for that module, with any extension identifying the content type left off.

For each module, set the ``name`` field to the page title to be displayed for that module. If no fields are provided and ``name`` is not set, the title for the module will be calculated from the name of the module file. The purpose of the ``exit_sign`` field will be discussed later when looking at page navigation.

The corresponding ``workshop/workshop.yaml`` file, where all available modules were being used, would have the format:

.. code-block:: yaml

    name: Markdown Sample

    modules:
        activate:
        - workshop-overview
        - setup-environment
        - exercises/01-sample-content
        - workshop-summary

The top level ``name`` field in this file is the name for this variation of the workshop content.

The ``modules.activate`` field is a list of modules to be used for the workshop. The names in this list must match the names as they appear in the modules file.

Specifying the runtime configuration
------------------------------------

Workshop images can be deployed directory to a container runtime. To manage deployments into a Kubernetes cluster, the eduk8s operator is provided. Configuration for the eduk8s operator is defined by a ``Workshop`` custom resource definition in the ``resources/workshop.yaml`` file:

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

The format of this file and others in the ``resources`` directory will be covered later in the part of the documentation which discusses the setup of a workshop environment under Kubernetes.
