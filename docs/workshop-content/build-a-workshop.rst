Build a Workshop
================

Bundling workshop content into an image built off the eduk8s ``workshop-dashboard`` image would be the typical way of distributing a workshop. This means the container image can be customised to include extra system or third party tools and/or configuration that may be required. For this purpose, the sample workshop templates provide a ``Dockerfile``.

Structure of the Dockerfile
---------------------------

The structure of the ``Dockerfile`` provided with the sample workshop templates is:

.. code-block:: text

    FROM quay.io/eduk8s/workshop-dashboard:master

    COPY --chown=1001:0 . /home/eduk8s/

A custom workshop image needs to be built on the ``quay.io/eduk8s/workshop-dashboard`` base image. This could be directly, or you could also create an intermediate base image if you needed to install extra packages which were required by a number of different workshops. You might for example create an intermediate base image which installed extra packages for working with the Java programming language.

The default action when building the container image when using the ``Dockerfile`` is to copy all files to the ``/home/eduk8s`` directory. The ``--chown=1001:0`` option ensures that files are owned by the appropriate user and group.

It is possible to include ``RUN`` statements in the ``Dockerfile`` to run custom build steps, but the ``USER`` inherited from the base image will be that having user ID ``1001`` and will not be the ``root`` user.

Container run as random user ID
-------------------------------

It is assumed that when a workshop is run, the container is run as the user ``1001`` that the workshop base image has set. This will be the case when a typical Kubernetes distribution is used, but some Kubernetes distributions such as OpenShift, enforce a pod security policy (or security context constraint) which forces pods in distinct namespaces to run as different assigned user IDs, overriding the default.

This can cause a problem if the workshop requires a user to run steps that need to write to the file system under ``/home/eduk8s``, and the location to be written to is a file copied into the image, or a sub directory. This is because the assigned user ID will not have the permissions to write to the files or directory.

If a step run during your workshop, or a setup script run when the container starts, needs to write to the file system, you will need to add to the ``Dockerfile``, after any files have been copied into the image or created by a ``RUN`` statement, a command to fix up permissions on the file system. This can be done using the statement:

.. code-block:: text

    RUN fix-permissions /home/eduk8s

This would usually be placed as the last statement in the ``Dockefile``. This command will ensure that group permissions for all files and directories are the same as the user permissions. This will allow group write access to work for the user the container image would be run as when not the intended user.

The alternative is to create a custom pod security policy specific to the session and add the service account the workshop instance run as, to that pod security policy. The custom pod security policy could then specify that the user set in the image could still be used by adding a rule of ``MustRunAsNonRoot``.

Note that this is only an issue if you wish to create workshop content that you want people to be able to run on a Kubernetes distribution such as OpenShift, which has a strict security policy which forces containers to run as a user ID different to what the container image specifies.

Installing extra system packages
--------------------------------

Installation of extra system packages requires the installation to be run as ``root``. To do this you will need to switch the user commands are run as before running the command. You should then switch the user back to user ID of ``1001`` when done.

.. code-block:: text

    USER root

    RUN ... commands to install system packages

    USER 1001

It is recommended you only use the ``root`` user to install extra system packages. Don't use the ``root`` user when adding anything under ``/home/eduk8s``. If you do you will need to ensure the user ID and group for directories and files are set to ``1001:0`` and then run the ``fix-permissions`` command if necessary.

One problem you should guard against though is that when running any command as ``root``, you should temporarily override the value of the ``HOME`` environment variable and set it to ``/root``.

If you don't do this, because the ``HOME`` environment variable is by default set to ``/home/eduk8s``, the ``root`` user may drop configuration files in ``/home/eduk8s``, thinking it is the ``root`` home directory. This can cause commands run later during the workshop to fail, if they try and update the same configuration files, as they will have wrong permissions.

Fixing the file and group ownership and running ``fix-permissions`` may help with this problem, but not always because of the strange permissions the ``root`` user may apply and how container image layers work. It is therefore recommended instead to always use:

.. code-block:: text

    USER root

    RUN HOME=/root && \
        ... commands to install system packages

    USER 1001

Installing third party packages
-------------------------------

If you are not using system packaging tools to install extra packages, but are instead manually downloading packages, and optionally compiling them to binaries, it is better to do this as the default user and not ``root``.

If compiling packages, it is recommended to always work in a temporary directory under ``/tmp`` and to remove the directory as part of the same ``RUN`` statement when done.

If what is being installed is just a binary, it can be installed into the ``/home/eduk8s/bin``. This directory is automatically in the application search path defined by the ``PATH`` environment variable for the image.

If you need to install a whole directory hierarchy of files, create a separate directory under ``/opt`` to install everything. You can then override the ``PATH`` environment variable in the ``Dockerfile`` to add any extra directory for application binaries and scripts, and the ``LD_LIBRARY_PATH`` environment variable for the location of shared libraries.
