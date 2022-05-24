(creating-a-workshop)=
Creating a Workshop
===================

To assist you if you want to create workshops with your own content, the Educates project provides a set of workshop templates from which new workshops can be created. The workshop templates can be downloaded to your own local computer and the provided script used to create a new workshop.

Downloading the workshop templates and using the script it includes provides the most flexibility as it allows you to select custom overlays to be applied to the base workshop for different use cases. If you are only after the most basic workshop, you can also create a workshop directly on GitHub by making use of GitHub's repository template feature.

Downloading the templates
-------------------------

If you have access to the GitHub `vmware-tanzu-labs` organization, to download the workshop template repository you can checkout a copy of the Git repository hosting the scripts by running:

```
git clone git@github.com:vmware-tanzu-labs/educates-workshop-templates.git
```

If you not have access to the GitHub `vmware-tanzu-labs` organization, instead run:

```
imgpkg pull -i ghcr.io/vmware-tanzu-labs/educates-workshop-templates:latest -o educates-workshop-templates
```

Generating the workshop
-----------------------

To generate a new workshop run the `create-workshop.sh` script provided with the workshop templates, passing a name for the workshop as argument.

```
educates-workshop-templates/create-workshop.sh lab-new-workshop
```

The name of the workshop must conform to what is valid for a RFC 1035 label name as detailed in [Kubernetes object name and ID](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/) requirements. That is:

* contain only lowercase alphanumeric characters or '-'
* start with an alphabetic character
* end with an alphanumeric character

Although a RFC 1035 label name allows for up to 63 characters, it is recommended that the name be restricted to 25 characters or less. This is because Educates will in various cases add a prefix or suffix to the name and if your name is too long, the name with prefix or suffix will exceed 63 characters and be rejected by Kubernetes in the situation it is being used.

By default the new workshop will be generated into a subdirectory of the current directory with same name as the workshop. If you wish to supply an alternate location for the parent directory for the workshop directory, use the `-o` or `--output` option.

Because the workshop name is used for the directory name, with the same name also being used when hosting the workshop as a Git repository on a service such as GitHub, it is recommended that workshop names always be prefixed with `lab-`. This ensures the directory or Git repository is more easily identified as being that for a workshop.

Deploying new workshop
----------------------

For convenience, the initial workshop content that was created includes a `Makefile` with targets for common tasks you will want to run when working on the workshop. These are set up specifically to work with Educates running in the local Kubernetes cluster created using the `educates-local-dev` package.

To deploy the workshop the first time, from within the workshop directory, in this case the `lab-new-workshop` directory, run:

```
make
```

This will trigger the two make targets of `publish-files` and `deploy-workshop`. The `publish-files` target will build an OCI image artefact containing the workshop content files and push it to the local image registry created with the local Kubernetes cluster. The `deploy-workshop` target deploys the workshop to the Kubernetes cluster. The deployed workshop will pull the workshop content files from the image registry for each workshop session.

To open your browser on the workshop, run:

```
make open-workshop
```

Alternatively, you can view the URL for the workshop by running:

```
kubectl get trainingportal/lab-new-workshop
```

You can check out the contents of the `Makefile` to understand what the targets do in case you want to run the commands directly.

Workshop content layout
-----------------------

The workshop template when used creates the following files in the top level directory:

* ``README.md`` - A file telling everyone what the workshop is about. Replace the current content provided in the sample workshop with your own.
* ``Dockerfile`` - Steps to build a custom workshop base image. This would be left as is, unless you want to customize it to install additional system packages or tools.
* ``Makefile`` - Configuration for make with targets for common operations for publishing and deploying workshop content when working locally.
* ``.dockerignore`` - List of files to ignore when building the workshop content into an image.

Key sub directories and the files contained within them are:

* ``workshop`` - Directory under which your workshop files reside.
* ``workshop/modules.yaml`` - Configuration file with details of available modules which make up your workshop, and data variables for use in content.
* ``workshop/workshop.yaml`` - Configuration file which provides the name of the workshop, the list of active modules for the workshop, and any overrides for data variables.
* ``workshop/content`` - Directory under which your workshop content resides, including images to be displayed in the content.
* ``resources`` - Directory under which Kubernetes custom resources are stored for deploying the workshop using Educates.
* ``resources/workshop.yaml`` - The custom resource for Educates which describes your workshop and requirements it may have when being deployed.
* ``resources/trainingportal.yaml`` - A sample custom resource for Educates for creating a training portal for the workshop, encompassing the workshop environment and a workshop instance.

A workshop may consist of other configuration files, and directories with other types of content, but this is the minimal set of files to get you started.

Root directory for exercises
----------------------------

Because of the proliferation of files and directories at the top level of the repository and thus potentially the home directory for the user when running the workshop environment, you can push files required for exercises during the workshop into the ``exercises`` sub directory below the root of the repository.

When such an ``exercises`` sub directory exists, the initial working directory for the embedded terminal when created will be set to be ``$HOME/exercises`` instead of ``$HOME``. Further, if the embedded editor is enabled, the sub directory will be opened as the workspace for the editor and only directories and files in that sub directory will be visible through the default view of the editor.

Note that the ``exercises`` directory isn't set as the home directory of the user. This means that if a user inadvertently runs ``cd`` with no arguments from the terminal, they will end up back in the home directory.

To try and avoid confusion and provide a means for a user to easily get back to where they need to be, it is recommended if instructing users to change directories, to always provide a full path relative to the home directory. Thus use a path of the form ``~/exercises/example-1`` rather than ``example-1``, to the ``cd`` command if changing directories. By using a full path, they can execute the command again and know they will end up back in the required location.

Modifying workshop content
--------------------------

After having made any changes to the workshop content, you want to test the changes, you need to rebuild the OCI image artefact containing the workshop content files.

Make a change to the instructions in the file `workshop/content/workshop-overview.md`. Then run:

```
make publish-files
```

If you are currently in a workshop session, end that session. Now create a new workshop session from the training portal. You should see the changes you have made.

For minor changes, instead of ending the workshop session and creating a new one, you can instead after publishing the update to the workshop content files, from the terminal inside of the workshop session, run:

```
update-workshop
```

This will pull a new copy of the workshop content files into the workshop session. You can then either refresh your browser window, or to update just the view of the current workshop instructions, hold down the `<SHIFT>` key while clicking on the reload icon in the top banner of the workshop session dashboard.

Modifying workshop definition
-----------------------------

If you need to modify the workshop definition found in the `resources/workshop.yaml` file and want to test those changes, you need to update the workshop definition in the Kubernetes cluster. To do this run:

```
make update-workshop
```

When this is done, if the changes would affect the workshop environment or what is setup for each workshop session, the old workshop environment will be shutdown and a new workshop environment started.

Once the update to the workshop definition has been triggered, if you are currently in a workshop session, end that session. Now create a new workshop session from the training portal.

Deleting the deployment
-----------------------

If you have stopped working on the workshop and wish to delete it from the Kubernetes cluster to preserve resources, you can run:

```
make delete-workshop
```
