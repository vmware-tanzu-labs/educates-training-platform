eduk8s
======

The **eduk8s** project provides a system for hosting interactive workshop environments in Kubernetes. It can be used for self paced or supervised workshops. It can also be useful where you need to package up demos of applications hosted in Kubernetes, for users or potential customers.

.. .. image:: dashboard.png

Users doing a workshop are provided access to a dashboard in their web browser combining a shell environment with the workshop content, including any custom tools required for the workshop. The dashboard can also optionally embed slide content, an IDE (Theia), a web console for accessing the Kubernetes cluster (Kubernetes dashboard, OpenShift web console, or Octant), and other custom web applications.

**Note that this documentation is in active development as we work towards a first official release. Not all functionality provided by eduk8s has been documented, so don't assume this is all there is. There is lots of goodies not fully documented yet and more in development.**

.. toctree::
  :maxdepth: 2
  :caption: Project Details:

  project-details/project-overview

.. toctree::
  :maxdepth: 2
  :caption: Getting Started:

  getting-started/installing-eduk8s
  getting-started/training-session
  getting-started/under-the-covers
  getting-started/deleting-eduk8s
  getting-started/sample-workshops

.. toctree::
  :maxdepth: 2
  :caption: Workshop Content:

  workshop-content/workshop-images
  workshop-content/workshop-config
  workshop-content/page-formatting
  workshop-content/workshop-runtime
  workshop-content/presenter-slides
  workshop-content/build-a-workshop

.. toctree::
  :maxdepth: 2
  :caption: Operator Config:

  runtime-environment/custom-resources
  runtime-environment/workshop-definition
  runtime-environment/workshop-environment
  runtime-environment/workshop-request
  runtime-environment/workshop-session
  runtime-environment/training-portal
