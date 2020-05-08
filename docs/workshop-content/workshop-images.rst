Workshop Images
===============

The workshop environment for eduk8s is packaged up as container image. You can execute the image with remote content pulled down from GitHub or a web server. Alternatively, you can bundle your workshop content, including any extra tools required, in a new container image derived from the workshop environment base image.

Templates for creating a workshop
---------------------------------

To get you started with your own workshop content, a number of sample Git repositories are provided. Which you use will depend on whether you prefer to use Markdown or AsciiDoc formatting for content. These are:

* https://github.com/eduk8s/lab-markdown-sample
* https://github.com/eduk8s/lab-asciidoc-sample

You have two options for how you can get started with these sample Git repositories.

The first option is to use the GitHub feature for creating a new repository from a `Git repository template <https://help.github.com/en/articles/creating-a-repository-from-a-template>`_. This is different to forking an existing Git repository on GitHub in that it creates a fresh repository with the latest content from the original Git repository. In creating a Git repository using this feature, it does not inherit any commit history from the original, and it is not linked to the original. Once you have created your copy of the Git repository, you can check out a copy to your own machine and start working on it.

The second option is to download a copy of one of the sample Git repositories from the releases page for that Git repository. From this you can then create a local Git repository, and push it up to a Git repository hosting service of your choice.

When creating your own workshops, a suggested convention is to always prefix the directory name, and thus the Git repository name where it is being hosted, with the ``lab-`` prefix. This way it stands out as a workshop or lab when you have a whole bunch of Git repositories on the same Git hosting service account or organisation.

Note that you should not make the name you use for a workshop too long, else the DNS host name used for applications deployed from the workshop, when using certain methods of deployment, may exceed the 63 character limit. This is because the workshop deployment name is used as part of the namespace for each workshop session, which will in turn be used in the DNS host names generated for the ingress hostname. It is suggested to keep the workshop name, and thus your repository name to 25 characters or less.

Workshop content directory layout
---------------------------------

When you have created a copy of the sample workshop content, you will see a number of files located in the top level directory, and a number of sub directories forming a hierarchy.

The files in the top level directory are:

* ``README.md`` - A file telling everyone what the workshop in your Git repository is about, and how to deploy it. Replace the current content provided in the sample workshop with your own.
* ``LICENSE`` - A license file so people are clear about how they can use your workshop content. Replace this with what license you want to apply to your workshop content.
* ``Dockerfile`` - Steps to build your workshop into an image ready for deployment. This would be left as is, unless you want to customize it to install additional system packages or tools.
* ``kustomization.yaml`` - A kustomize resource file for loading the workshop definition. When using this, the eduk8s operator still needs to have first been deployed.
* ``.dockerignore`` - List of files to ignore when building the workshop content into an image.
* ``.eduk8signore`` - List of files to ignore when downloading workshop content into the workshop environment at runtime.

Key sub directories and the files contained within them are:

* ``workshop`` - Directory under which your workshop files reside.
* ``workshop/modules.yaml`` - Configuration file with details of available modules which make up your workshop, and data variables for use in content.
* ``workshop/workshop.yaml`` - Configuration file which provides the name of the workshop, the list of active modules for the workshop, and any overrides for data variables.
* ``workshop/content`` - Directory under which your workshop content resides, including images to be displayed in the content.
* ``resources`` - Directory under which Kubernetes custom resources are stored for deploying the workshop using eduk8s.
* ``resources/workshop.yaml`` - The custom resources for eduk8s which describes your workshop and requirements it may have when being deployed.
* ``resources/training-portal.yaml`` - A sample custom resource for eduk8s for creating a training portal for the workshop, encompassing the workshop environment and a workshop instance.

A workshop may consist of other configuration files, and directories with other types of content, but this is the minimal set of files to get you started.
