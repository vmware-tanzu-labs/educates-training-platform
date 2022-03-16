educates
========

The **educates** project provides a system for hosting interactive workshop environments in Kubernetes. It can be used for self paced or supervised workshops. It can also be useful where you need to package up demos of applications hosted in Kubernetes for users or potential customers.

Users doing a workshop are provided access to a dashboard in their web browser combining a shell environment with the workshop content, including any custom tools required for the workshop. The dashboard can also optionally embed slide content, an IDE, a web console for accessing the Kubernetes cluster (Kubernetes dashboard or Octant), and other custom web applications. Where required for a workshop, deployment of an image registry per workshop session, and the ability to use docker for doing container image builds, can be enabled.


.. toctree::
  :maxdepth: 2
  :caption: Project Details:

  project-details/project-overview
  project-details/sample-screenshots

.. toctree::
  :maxdepth: 2
  :caption: Installation Guides:

  installation-guides/installing-operator
  installation-guides/training-session
  installation-guides/under-the-covers
  installation-guides/deleting-operator
  installation-guides/sample-workshops
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
