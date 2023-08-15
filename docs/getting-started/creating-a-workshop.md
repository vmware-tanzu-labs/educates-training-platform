(creating-a-workshop)=
Creating a Workshop
===================

To assist you if you want to create workshops with your own content, the Educates command line tool bundles a template which can be used to create a new workshop.

Generating the workshop
-----------------------

To generate a new workshop run the `educates new-workshop` command, passing it as argument a directory path to where the workshop content should be placed.

```
educates new-workshop lab-new-workshop
```

The last component of the supplied path will be used as the workshop name.

As the workshop name must conform to what is valid for a RFC 1035 label name, as detailed in [Kubernetes object name and ID](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/), the last component of the supplied path should:

* contain only lowercase alphanumeric characters or '-'
* start with an alphabetic character
* end with an alphanumeric character

Although a RFC 1035 label name allows for up to 63 characters, it is recommended that the name be restricted to 25 characters or less. This is because Educates will in various cases add a prefix or suffix to the name and if your name is too long, the name with prefix or suffix will exceed 63 characters and be rejected by Kubernetes in the situation it is being used.

If you are hosting the workshop content in a Git hosting service such as GitHub, the name of the hosted Git repository must match the name of the workshop if you intend making use of the GitHub actions supplied by the Educates project for publishing workshops.

It is also recommended that workshop names always be prefixed with `lab-`. This ensures the directory or Git repository is more easily identified as being that for a workshop amongst any other Git repositories.

Rendering of instructions
-------------------------

Educates currently supports two different renderers for workshop instructions. The first and original renderer for workshop instructions included in Educates is called the `classic` renderer. This is a custom dynamic web application for rendering the workshop instructions. It supports the use of Markdown or AsciiDoc.

When you you ran `educates new-workshop` it defaulted to generating configuration and instructions files for Markdown using the `classic` renderer.

The second renderer for workshop instructions is the `hugo` renderer. As the name suggests this makes use of [Hugo](https://gohugo.io/) to generate workshop instructions as static HTML files, using custom layouts provided by Educates. Hugo only supports the use of Markdown.

If you want to generate a new workshop which uses the `hugo` renderer, run the `educates new-workshop` command as:

```
educates new-workshop lab-new-workshop --template hugo
```

The `hugo` renderer was introduced in Educates version 2.6.0. It is expected that in time the `classic` renderer will be deprecated and the `hugo` renderer will be the recommended option.

Deploying new workshop
----------------------

To deploy a new workshop, from within the workshop directory, in this case the `lab-new-workshop` directory, first run:

```
educates publish-workshop
```

This will build an OCI image artifact containing the workshop content files and push it to the local image registry created with the local Kubernetes cluster.

You can then create the workshop environment in the Kubernetes cluster by running:

```
educates deploy-workshop
```

The deployed workshop will pull the workshop content files published to the image registry for each workshop session.

To access the training portal from your web browser and select the workshop, run:

```
educates browse-workshops
```

If necessary, you can view the password for accessing the training portal instance by running:

```
educates view-credentials
```

Workshop content layout
-----------------------

The workshop template when used creates the following files in the top level directory:

* ``README.md`` - A file telling everyone what the workshop is about. Replace the current content provided in the sample workshop with your own.

Key sub directories and the files contained within them are:

* ``workshop`` - Directory under which your workshop files reside.
* ``workshop/content`` - Directory under which your workshop instructions resides.
* ``resources`` - Directory under which Kubernetes custom resources are stored for deploying the workshop using Educates.
* ``resources/workshop.yaml`` - The custom resource for Educates which describes your workshop and requirements it may have when being deployed.

If you are using the `classic` renderer for workshop instructions you would also have the following files:

* ``workshop/modules.yaml`` - Configuration file with details of available modules which make up your workshop, and data variables for use in content.
* ``workshop/workshop.yaml`` - Configuration file which provides the name of the workshop, the list of active modules for the workshop, and any overrides for data variables.

If you are using the `hugo` renderer, instead of ``workshop/modules.yaml`` and ``workshop/workshop.yaml`` you may optionally have the single file:

* ``workshop/config.yaml`` - Configuration file with details of available modules which make up your workshop, data variables for use in content, and selectable paths through the workshop instructions.

In the case of the `hugo` renderer, if `workshop/config.yaml` doesn't exist or no configuration is included within it, workshop instructions page ordering will be based on file name sort order, or page weights if defined in the meta data of pages.

If your workshop instructions use images, if using the `classic` renderer, the images can be placed in the same directory as the Markdown or AsciiDoc files. If using the `hugo` renderer, you should follow the Hugo convention and place images in the `workshop/static` directory, or use page bundles and include the image for a page in the directory for the page bundle.

A workshop may consist of other configuration files, and directories with other types of content, but this is the minimal set of files to get you started.

Root directory for exercises
----------------------------

Because of possible proliferation of files and directories at the top level of the repository and thus potentially the home directory for the user when running the workshop environment, you can place files required for exercises during the workshop into the ``exercises`` sub directory below the root of the repository.

When such an ``exercises`` sub directory exists, the initial working directory for the embedded terminal when created will be set to be ``$HOME/exercises`` instead of ``$HOME``. Further, if the embedded editor is enabled, the sub directory will be opened as the workspace for the editor and only directories and files in that sub directory will be visible through the default view of the editor.

Note that the ``exercises`` directory isn't set as the home directory of the user. This means that if a user inadvertently runs ``cd`` with no arguments from the terminal, they will end up back in the home directory.

To try and avoid confusion and provide a means for a user to easily get back to where they need to be, it is recommended if instructing users to change directories, to always provide a full path relative to the home directory. Thus use a path of the form ``~/exercises/example-1`` rather than ``example-1``, to the ``cd`` command if changing directories. By using a full path, they can execute the command again and know they will end up back in the required location.

(modifying-workshop-content)=
Modifying workshop content
--------------------------

After having made any changes to the workshop content you want to test the changes, you need to rebuild the OCI image artifact containing the workshop content files.

Make a change to the instructions in the file `workshop/content/00-workshop-overview.md`. Then run:

```
educates publish-workshop
```

If you are currently in a workshop session, end that session. Now create a new workshop session from the training portal. You should see the changes you have made.

For minor changes, instead of ending the workshop session and creating a new one, you can instead after publishing the update to the workshop content files, from the terminal inside of the workshop session, run:

```
update-workshop
```

This will pull a new copy of the workshop content files into the workshop session. You can then either refresh your browser window, or to update just the view of the current workshop instructions, hold down the `<SHIFT>` key while clicking on the reload icon in the top banner of the workshop session dashboard.

The above process for modifying and updating workshop content will work if using either the `classic` or `hugo` renderers for workshop instructions.

If you are using the `hugo` renderer, you can also activate a live reload mode for workshop instructions. To activate this run:

```
educates serve-workshop --patch-workshop
```

This command will patch the workshop definition which exists in the cluster, triggering the deployment of a new workshop environment, where workshop sessions will be configured to connect back and load workshop instructions from a web server run by the `educates serve-workshop` command.

To access the workshop, as before create a new workshop session from the training portal. When you now modify the local copy of any pages making up the workshop instructions, the view of the instructions will be automatically regenerated and the browser page refreshed to show the latest version, without needing to republish the workshop content.

Once you have tested the local changes and are happy with them, you can interrupt and exit the `educates serve-workshop` process using `<CTRL-C>`. This will cause the workshop definition in the cluster to be restored and the published version of the workshop once more used. Then republish the workshop using `educates publish-workshop` and the updated content will then be used for subsequent workshop sessions created from the training portal.

Note that the patched workshop configuration created when using the `--patch-workshop` option will only source workshop instructions from the local machine. If you have other workshop files such as setup scripts or code files to be used in exercises, it will still be necessary to go through the process of republishing the workshop content and creating a new workshop session so the changes are picked up. 

Modifying workshop definition
-----------------------------

If you need to modify the workshop definition found in the `resources/workshop.yaml` file and want to test those changes, you need to update the workshop definition in the Kubernetes cluster. To do this run:

```
educates update-workshop
```

When this is done, if the changes would affect the workshop environment or what is setup for each workshop session, the old workshop environment will be shutdown and a new workshop environment started.

Once the update to the workshop definition has been triggered, if you are currently in a workshop session, end that session. Now create a new workshop session from the training portal.

Deleting the deployment
-----------------------

If you have stopped working on the workshop and wish to delete it from the Kubernetes cluster to preserve resources, you can run:

```
educates delete-workshop
```
