Learning Center
===============

The Learning Center platform integrated into the Tanzu Application Platform is a copy/fork of Educates taken at the beginning of 2021. Work on Educates was suspended at that time, but to meet the needs of Tanzu Developer Center and KubeAcademy, development work on Educates was restarted at the beginning on 2022. The development of Educates and Learning Center now run independently.

Separate modifications have been made to both Learning Center and Educates which means that workshops cannot be migrated between them without changes.

The following lists some of the known incompatibilities between the two platforms. The list does not cover all differences as the ongoing maintainers of Educates do not have direct knowledge of the changes that have been made to Learning Center, and so can only list incompatibilities arising from changes in Educates, or more obvious changes in Learning Center.

Kubernetes resource versions
----------------------------

The api group name and version for Kubernetes resources used to describe and deploy workshops was changed in Learning Center.

Because of this change in Learning Center, you will need to keep two separate versions of the resources, or use `ytt` templates to dynamically generate the appropriate resource definition based on the target platform, if wishing to support using workshop content on both platforms.

Upgrade of VS Code version
--------------------------

Educates has been updated to use the latest major update of VS Code package from [Coder](https://github.com/coder/code-server). This is version v4.x vs the previously used v3.x version.

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

Fixup of OCI artefact permissions
---------------------------------

The `imgpkg` program from Carvel used to package up workshop content as an OCI artefact, allowing it to be used as the source of workshop content, does not preserve the original file permissions for group and others. This can cause problems where workshop content contains files used as input to `docker` image builds and permissions on files are important. Loss of the permissions can for example result in files copied into an image not being accessible when the container image runs as a non `root` user.

To workaround this limitation with `imgpkg`, Educates when it detects group and other permissions do not exist, will copy those permissions from the user permissions (except for write permission).

Because of this change in Educates, if migrating workshop content from Educates to Learning Center, it may not work in Learning Center.
