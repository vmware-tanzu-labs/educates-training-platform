Building an Image
=================

Although it is recommended to use [extension packages](adding-extension-packages) to bundle up additional applications needed by workshops, and overlay those on the standard workshop base image when a workshop session is started, it is possible to build your own custom workshop base images. Because this results in a hard dependency on a specific version of the workshop base image, it can result in workshop images which may not work with a newer Educates version. As such, only use this ability if you feel there is no other choice.

Structure of the Dockerfile
---------------------------

The structure of the ``Dockerfile`` to build a custom workshop base image should start out as:

```text
FROM ghcr.io/vmware-tanzu-labs/educates-base-environment:2.6

COPY --chown=1001:0 . /home/eduk8s/

RUN mv /home/eduk8s/workshop /opt/workshop

RUN fix-permissions /home/eduk8s
```

A custom workshop image needs to be built on the ``ghcr.io/vmware-tanzu-labs/educates/base-environment`` workshop image.

Where the custom workshop image will also include files for a specific workshop, the default actions you include when building the container image should include copying all files to the ``/home/eduk8s`` directory. The ``--chown=1001:0`` option ensures that files are owned by the appropriate user and group. The ``workshop`` subdirectory is then moved to ``/opt/workshop`` so that it is out of the way and not visible to the user. This is a special location which will be searched for workshop content, in addition to ``/home/eduk8s/workshop``. To have other files or directories from the repository ignored, list them in the ``.dockerignore`` file.

It is possible to include ``RUN`` statements in the ``Dockerfile`` to run custom build steps, but the ``USER`` inherited from the base image will be that having user ID ``1001`` and will not be the ``root`` user.

Bases images and version tags
-----------------------------

The sample ``Dockerfile`` provided above references the workshop base image as:

```
ghcr.io/vmware-tanzu-labs/educates-base-environment:2.6
```

This needs to be changed and the version kept up to date and match the version of Educates you want to use.

To see what versions are available of the ``base-environment`` image visit:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-base-environment](https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-base-environment)

Custom workshop base images
---------------------------

The ``base-environment`` workshop images include language run times for Node.js and Python. If you need a different language runtime, or need a different version of a language runtime, you will need to use a custom workshop base image which includes the supported environment you need. This custom workshop image would be derived from ``base-environment`` but include the extra runtime components needed.

For using the Java programming language, the Educates project provides separate custom workshop images for JDK 8, 11 and 17. In addition to including the respective Java runtimes, they include Gradle and Maven.

The name of the JDK 8 version of the Java custom workshop base image is:

```
ghcr.io/vmware-tanzu-labs/educates-jdk8-environment:2.6
```

To see what specific tagged version of the image exist visit:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk8-environment](https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk8-environment)

The name of the JDK 11 version of the Java custom workshop base image is:

```
ghcr.io/vmware-tanzu-labs/educates-jdk11-environment:2.6
```

To see what specific tagged version of the image exist visit:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk11-environment](https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk11-environment)

The name of the JDK 17 version of the Java custom workshop base image is:

```
ghcr.io/vmware-tanzu-labs/educates-jdk17-environment:2.6
```

To see what specific tagged version of the image exist visit:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk17-environment](https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk17-environment)

The name of the JDK 21 version of the Java custom workshop base image is:

```
ghcr.io/vmware-tanzu-labs/educates-jdk21-environment:2.6
```

To see what specific tagged version of the image exist visit:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk21-environment](https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-jdk21-environment)

The images will be updated over time to try and include the latest versions of Gradle and Maven. In case you are using Gradle or Maven wrapper scripts for selecting a specific version of these tools, configuration for these wrapper scripts is provided for the pre-installed version to avoid it being downloaded again.

If wanting to run workshops based around using Anaconda Python or Jupyter notebooks, the Educates project provides a suitable base environment.

The name of the Anaconda workshop base image is:

```
ghcr.io/vmware-tanzu-labs/educates-conda-environment:2.6
```

To see what specific tagged version of the image exist visit:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-conda-environment](https://github.com/vmware-tanzu-labs/educates-training-platform/pkgs/container/educates-conda-environment)

Container run as random user ID
-------------------------------

It is assumed that when a workshop is run, the container is run as the user ``1001`` that the workshop base image has set. This will be the case when a typical Kubernetes distribution is used, but some Kubernetes distributions such as OpenShift, may enforce a pod security policy (or security context constraint) which forces pods in distinct namespaces to run as different assigned user IDs, overriding the default.

This can cause a problem if the workshop requires a user to run steps that need to write to the file system under ``/home/eduk8s``, and the location to be written to is a file copied into the image, or a sub directory. This is because the assigned user ID will not have the permissions to write to the files or directory.

To cope with this, a setup script called ``fix-permissions`` is included in the base image and is executed as the final step from the ``Dockerfile``. This command will ensure that group permissions for all files and directories are the same as the user permissions. This will allow group write access to work for the user the container image would be run as when not the intended user.

Note that this is only an issue if you wish to create workshop content that you want people to be able to run on a Kubernetes distribution such as OpenShift, which has a strict security policy which forces containers to run as a user ID different to what the container image specifies.

Note that this OpenShift issue may no longer exist due to changes in Educates, but is good practice all the same.

Installing extra system packages
--------------------------------

Installation of extra system packages requires the installation to be run as ``root``. To do this you will need to switch the user commands are run as before running the command. You should then switch the user back to user ID of ``1001`` when done.

```text
USER root

RUN ... commands to install system packages

USER 1001
```

It is recommended you only use the ``root`` user to install extra system packages. Don't use the ``root`` user when adding anything under ``/home/eduk8s``. If you do you will need to ensure the user ID and group for directories and files are set to ``1001:0`` and then run the ``fix-permissions`` command if necessary.

One problem you should guard against though is that when running any command as ``root``, you should temporarily override the value of the ``HOME`` environment variable and set it to ``/root``.

If you don't do this, because the ``HOME`` environment variable is by default set to ``/home/eduk8s``, the ``root`` user may drop configuration files in ``/home/eduk8s``, thinking it is the ``root`` home directory. This can cause commands run later during the workshop to fail, if they try and update the same configuration files, as they will have wrong permissions.

Fixing the file and group ownership and running ``fix-permissions`` may help with this problem, but not always because of the strange permissions the ``root`` user may apply and how container image layers work. It is therefore recommended instead to always use:

```text
USER root

RUN HOME=/root && \
    ... commands to install system packages

USER 1001
```

Installing third party packages
-------------------------------

If you are not using system packaging tools to install extra packages, but are instead manually downloading packages, and optionally compiling them to binaries, it is better to do this as the default user and not ``root``.

If compiling packages, it is recommended to always work in a temporary directory under ``/tmp`` and to remove the directory as part of the same ``RUN`` statement when done.

If what is being installed is just a binary, it can be installed into the ``/home/eduk8s/bin``. This directory is automatically in the application search path defined by the ``PATH`` environment variable for the image.

If you need to install a whole directory hierarchy of files, create a separate directory under ``/opt`` to install everything. You can then override the ``PATH`` environment variable in the ``Dockerfile`` to add any extra directory for application binaries and scripts, and the ``LD_LIBRARY_PATH`` environment variable for the location of shared libraries.

If installing any files from a ``RUN`` instruction into ``/home/eduk8s``, it is recommended you run ``fix-permissions`` as part of the same instruction to avoid copies of files being made into a new layer, which would be the case if ``fix-permissions`` is only run in a later ``RUN`` instruction. You can still leave the final ``RUN`` instruction for ``fix-permissions`` as it is smart enough not to apply changes if the file permissions are already set correctly, and so it will not trigger a copy of a file when run more than once.
