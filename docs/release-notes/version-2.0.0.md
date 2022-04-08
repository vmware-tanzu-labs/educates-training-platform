Version 2.0.0
=============

Note: The version of Educates which was used as the basis for the Learning Center platform integrated into the Tanzu Application Platform is regarded as being version 1.X. Version 2.0.0 is the first release of Educates after development was restarted.

Bugs Fixed
----------

### Fixup of OCI artefact permissions

The `imgpkg` program from Carvel used to package up workshop content as an OCI artefact, allowing it to be used as the source of workshop content, does not preserve the original file permissions for group and others. This can cause problems where workshop content contains files used as input to `docker` image builds and permissions on files are important. Loss of the permissions can for example result in files copied into an image not being accessible when the container image runs as a non `root` user.

To workaround this limitation with `imgpkg`, Educates now detects when group and other permissions do not exist, and will copy those permissions from the user permissions (except for write permission).

### Downloading workshops from GitHub

Educates allows the workshop content files to be downloaded from GitHub using `files` set to `github.com/organization/repository:branch`. If `branch` is left off then `master` branch would be tried first, and then `main`. GitHub however changed behaviour such that downloading the tar ball for `master` would redirect to that for `main` if `master` wasn't a valid branch. When unpacking this tar ball, the root directory would be `main` and not the expected `master`, causing a failure.

To workaround this change in GitHub, Educates now tries `main` before `master` if no branch is explicitly provided.

### Binding of system service ports

A workshop specifying `anyuid` for the namespace security policy was able to run pods as `root`, however they weren't able to bind low numbered system service ports. This restriction has been removed, allowing a pod running as `root` to bind port 80 for HTTP web servers.

### Custom namespace resource quotas

When using a `custom` resource budget for namespaces in order to define `ResourceQuotas` explicitly for the session namespaces, the code which verified that the resource quotas had been accepted by the API server and acknowledged by updating the hard quota in the status, was failing because code hadn't been updated correctly to the newer Kubernetes Python client API. Use of `custom` for the `budget` should now work correctly.

### Redirection to the web site root

If a direct link to a workshop session is saved away or shared with another user, and later used to access the training portal when there is no active login, the user would be redirected to the login page even if the training portal had anonymous access enabled. In this situation the user will instead now be redirected initially to the root of the web site. In this case if anonymous access is enabled they should then be redirected to the workshop catalog, or if an event code or login is necessary, they will be directed to the appropriate page to login.

Features Changed
----------------

### System profiles must exist

Previously if the operator believed a named system profile didn't yet exist, perhaps because the operator hadn't yet processed it, processing of the resources for a `TrainingPortal` would still proceed, meaning that the incorrect configuration could be used when the operator is first deployed or is starting. This also occurred in the case of the implicit default system configuration.

To combat this issue resources will now only be processed if the corresponding named system profile exists. In the case of `default-system-profile`, it is now explicitly set as the named default in the operator deployment using the `SYSTEM_PROFILE` environment variable. There is no longer an implicit default system profile.

The only default configuration values that can be set for all system profiles are for the ingress domain, secret and class, which are set via their own environment variables. The default deployment resources will rely on the environment variables for setting these instead of setting them in `default-system-profile`.

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

### OpenShift client and console

Client tools for working with OpenShift, including support for the OpenShift web console were removed.

New Features
------------

### Analytics events for actions

A clickable action in the workshop instructions can be designated as an event source for analytics delivered by the analytics webhook defined for a training portal. For more information see:

* [Generating events for actions](generating-events-for-actions)
* [Collecting analytics on workshops](collecting-analytics-on-workshops)

### Clickable actions in Javascript

The functionality of a subset of clickable actions can be accessed from web pages or web sites embedded in a dashboard tab, using Javascript messages. For more information see:

* [Triggering actions from Javascript](triggering-actions-from-javascript)
