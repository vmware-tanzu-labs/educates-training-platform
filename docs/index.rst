Educates
========

The **Educates** project provides a system for hosting interactive workshop environments in Kubernetes. It can be used for self paced or supervised workshops. It can also be useful where you need to package up demos of applications hosted in Kubernetes for users or potential customers.

Note that the Learning Center platform integrated into the Tanzu Application Platform (TAP) is a copy/fork of Educates made at the beginning of 2021. Work on Educates was suspended at that time, but to meet the needs of Tanzu Developer Center and KubeAcademy, development work on Educates was restarted at the beginning of 2022. The development of Educates and Learning Center now run independently. This documentation is therefore targeted specifically at anyone needing to create workshop content for Tanzu Developer Center or KubeAcademy. If you are wanting to create workshops for your own internal use, with partners or customers, the official supported solution for that is Learning Center. If you are after documentation for Tanzu Learning Center check out the `TAP documentation <https://docs.vmware.com/en/Tanzu-Application-Platform/1.1/tap/GUID-learning-center-about.html>`_.

.. toctree::
  :maxdepth: 2
  :caption: Project Details:

  project-details/project-overview
  project-details/sample-screenshots

.. toctree::
  :maxdepth: 2
  :caption: Getting Started:

  getting-started/quick-start-guide
  getting-started/creating-a-workshop
  getting-started/workshop-templates
  getting-started/local-environment
  getting-started/sample-workshops

.. toctree::
  :maxdepth: 2
  :caption: Installation Guides:

  installation-guides/installing-operator
  installation-guides/training-session
  installation-guides/under-the-covers
  installation-guides/deleting-operator
  installation-guides/deploying-to-minikube
  installation-guides/deploying-to-kind

.. toctree::
  :maxdepth: 2
  :caption: Workshop Content:

  workshop-content/workshop-images
  workshop-content/workshop-config
  workshop-content/workshop-instructions
  workshop-content/workshop-runtime
  workshop-content/presenter-slides
  workshop-content/building-an-image
  workshop-content/working-on-content

.. toctree::
  :maxdepth: 2
  :caption: Operator Config:

  runtime-environment/custom-resources
  runtime-environment/workshop-definition
  runtime-environment/workshop-environment
  runtime-environment/workshop-request
  runtime-environment/workshop-session
  runtime-environment/training-portal
  runtime-environment/system-profile

.. toctree::
  :maxdepth: 2
  :caption: Portal REST API:

  portal-rest-api/client-authentication
  portal-rest-api/workshops-catalog
  portal-rest-api/session-management
  portal-rest-api/anonymous-access

.. toctree::
  :maxdepth: 2
  :caption: Workshop Migration:

  workshop-migration/learning-center

.. toctree::
  :maxdepth: 2
  :caption: Release Notes:

  release-notes/version-2.0.0
