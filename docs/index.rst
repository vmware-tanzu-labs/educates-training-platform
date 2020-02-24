eduk8s
======

The **eduk8s** project provides a system for hosting interactive workshop environments in Kubernetes. It can be used for self paced or supervised workshops where users need access to command line clients and other tools when working with Kubernetes. It can also be useful where you need to package up demos of applications hosted in Kubernetes, for users or potential customers.

.. image:: dashboard.png

Users are provided access to a dashboard combining the workshop content and a shell environment, via a terminal in their web browser. The dashboard can also embed the Kubernetes web console, slide content, or custom web applications.

**Note that this documentation is in active development as we work towards a first official release. Not all functionality provided by eduk8s has been documented, so don't assume this is all there is. There is lots of goodies not fully documented yet and more in development.**

.. toctree::
  :maxdepth: 2
  :caption: Getting Started:

  getting-started/installing-eduk8s
  getting-started/training-session
  getting-started/under-the-covers
  getting-started/deleting-eduk8s

.. toctree::
  :maxdepth: 2
  :caption: Workshop Content:

  workshop-content/workshop-images
  workshop-content/workshop-config
  workshop-content/page-formatting
  workshop-content/presenter-slides
  workshop-content/build-a-workshop
  workshop-content/workshop-runtime

.. toctree::
  :maxdepth: 2
  :caption: Operator Config:

  runtime-environment/custom-resources
  runtime-environment/workshop-definition
  runtime-environment/workshop-environment
  runtime-environment/workshop-request
  runtime-environment/workshop-session
  runtime-environment/training-portal
