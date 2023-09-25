Developer Documentation
=======================

The Educates project consists of the following Git repositories:

* Educates Training Platform - https://github.com/vmware-tanzu-labs/educates-training-platform
* Educates Packages Repository - https://github.com/vmware-tanzu-labs/educates-packages
* Educates GitHub Actions - https://github.com/vmware-tanzu-labs/educates-github-actions

Educates Training Platform (this repository), holds all source code for building and making releases of the core platform.

Educates Packages Repository holds the definitions used to generate the Carvel packages from which Educates can be installed using the Carvel ``kapp-controller`` operator.

Educates User Documentation holds the source files for user documentation hosted on https://docs.educates.dev/.

Educates GitHub Actions holds GitHub actions to assist in publishing workshops to GitHub container registry.

If wanting to contribute to Educates, you can build and deploy a local copy of Educates by following the [build instructions](build-instructions.md).

For details on the design of Educates and how it works check out notes on it's [platform architecture](platform-architecture.md).

If you want to learn about future directions the Educates project may take, check out the [project roadmap](project-roadmap.md).

For maintainers, steps required to create a release of Educates are detailed in the [release procedures](release-procedures.md).
