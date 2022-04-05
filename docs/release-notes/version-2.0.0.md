Version 2.0.0
=============

Note: The version of Educates which was used as the basis for the Learning Center platform integrated into the Tanzu Application Platform is regarded as being version 1.X. Version 2.0.0 is the first release of Educates after development was restarted.

Bugs Fixed
----------

### Fixup of OCI artefact permissions

The `imgpkg` program from Carvel used to package up workshop content as an OCI artefact, allowing it to be used as the source of workshop content, does not preserve the original file permissions for group and others. This can cause problems where workshop content contains files used as input to `docker` image builds and permissions on files are important. Loss of the permissions can for example result in files copied into an image not being accessible when the container image runs as a non `root` user.

To workaround this limitation with `imgpkg`, Educates now detects when group and other permissions do not exist, and will copy those permissions from the user permissions (except for write permission).

Features Changed
----------------

### Third party software upgrades

Versions of third party packages used by Educates were updated to latest available at the time. This includes Carvel tools, Kubernetes dashboard, `kustomize`, `helm`, `skaffold` etc.

The `kubectl` versions currently provided are 1.20 through 1.23.

### Upgrade of VS Code version

Educates was updated to use the latest major update of VS Code package from [Coder](https://github.com/coder/code-server). This is version v4.x vs the previously used v3.x version.

Due to changes in how the newer version of VS Code handles extensions, Educates no longer installs any editor extensions by default. It is therefore up to a specific workshop to install the editor extensions they want to use.

Installation of editor extensions can be done from a `workshop/setup.d` file when the workshop container starts.

You can either directly install the extension from the [Open VSX Registry](https://open-vsx.org/), or bundle the `vsix` file with the workshop assets and install it from the local file system

If for example you were running a Java workshop, you might include an executable setup script file in `workshop/setup.d` containing:

```
#!/bin/bash

set +x

/opt/code-server/bin/code-server --install-extension Pivotal.vscode-spring-boot@1.30.0
/opt/code-server/bin/code-server --install-extension redhat.java@1.3.0
/opt/code-server/bin/code-server --install-extension vscjava.vscode-java-debug@0.38.0
/opt/code-server/bin/code-server --install-extension vscjava.vscode-java-dependency@0.19.0
/opt/code-server/bin/code-server --install-extension vscjava.vscode-java-test@0.34.1
/opt/code-server/bin/code-server --install-extension vscjava.vscode-maven@0.35.0
/opt/code-server/bin/code-server --install-extension vscjava.vscode-spring-initializr@0.8.0
```

If you didn't want to automate installation of extensions, you could just instruct a user to install the extension themselves via the VS Code interface as part of the workshop instructions.

Note that one of the reasons that editor extensions are no longer installed by default is because some extensions have significant memory resource requirements even when not being used. This is the case for the Java extension. You should therefore only install an editor extension if you absolutely need it and it is used by the workshop.

Because of this change in Educates, if migrating workshop content from Learning Center to Educates, you will need to install any required editor extensions, which were previously bundled by default, as part of your workshop setup.

### OpenShift client and console

Client tools for working with OpenShift, including support for the OpenShift web console were removed.

New Features
------------

### Analytics events for actions

A clickable action in the workshop instructions can be designated as an event source for analytics delivered by the analytics webhook defined for a training portal. For more information see:

* [Generating events for actions](generating-events-for-actions)
* [Collecting analytics on workshops](collecting-analytics-on-workshops)
