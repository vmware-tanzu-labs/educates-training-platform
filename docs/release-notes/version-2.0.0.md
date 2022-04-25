Version 2.0.0
=============

Note: The version of Educates which was used as the basis for the Learning Center platform integrated into the Tanzu Application Platform is regarded as being version 1.X. Version 2.0.0 is the first release of Educates after development was restarted.

Bugs Fixed
----------

### Fixup of OCI artefact permissions

The `imgpkg` program from Carvel used to package up workshop content as an OCI artefact, allowing it to be used as the source of workshop content, does not preserve correctly the original file permissions for group and others. This can cause problems where workshop content contains files used as input to `docker` image builds and permissions on files are important. Loss of the permissions can for example result in files copied into an image not being accessible when the container image runs as a non `root` user. To workaround this limitation with `imgpkg`, Educates copies permissions from the user (except for write permission) to group and other in situations where `imgpkg`, including via `vendir`, is used.

Note that the underlying issue was in part addressed in `imgpkg` version 0.28.0, but the parent directory permissions were still not being fixed properly so the adjustment is still being performed for now.

### Downloading workshops from GitHub

Educates allows the workshop content files to be downloaded from GitHub by setting `spec.content.files` in the workshop definition to `github.com/organization/repository:branch`. If `branch` is left off then `master` branch would be tried first, and then `main`. GitHub however changed behaviour such that downloading the tar ball for `master` would redirect to that for `main` if `master` wasn't a valid branch. When unpacking this tar ball, the root directory would be `main` and not the expected `master`, causing a failure. To workaround this change in GitHub, Educates now tries `main` before `master` if no branch is explicitly provided.

Note that despite this fix specifying workshop content to download by specifying `spec.content.files` is now deprecated and you should use `spec.content.downloads` and the `vendir` based download mechanism instead.
### Binding of system service ports

A workshop specifying `anyuid` for the session namespace security policy was able to run pods as `root`, however they weren't able to bind low numbered system service ports. This restriction has been removed, allowing a pod running as `root` to bind port 80 for HTTP web servers.

### Custom namespace resource quotas

When using a `custom` resource budget for namespaces in order to define `ResourceQuotas` explicitly for the session namespaces, the code which verified that the resource quotas had been accepted by the API server and acknowledged by updating the hard quota in the status, was failing because code hadn't been updated correctly to the newer Kubernetes Python client API. Use of `custom` for the `budget` should now work correctly.

### Redirection to the web site root

If a direct link to a workshop session is saved away or shared with another user, and later used to access the training portal when there is no active login, the user would be redirected to the login page even if the training portal had anonymous access enabled. In this situation the user will instead now be redirected initially to the root of the web site. In this case if anonymous access is enabled they should then be redirected to the workshop catalog, or if an event code or login is necessary, they will be directed to the appropriate page to login.

### Missing session ID variable

The `session_id` variable could be used within the `Workshop` definition, but was not available for use as a data variable in workshop instructions or as an environment variable in the workshop container shell environment.

Features Changed
----------------

### System profiles no longer exist

The concept of system profiles and the `SystemProfile` resource have been removed. Only a single global configuration now exists which is configured through the data values supplied when deploying Educates.

### Resource naming changes

The name of the namespace into which the operator for managing workshop sessions is deployed has changed from `eduk8s` to `educates`. The name of the operator deployment was in the process changed from `eduk8s-operator` to `session-manager`. The name of the deployment for a training portal was also changed from `eduk8s-portal` to `training-portal`.

Naming for any cluster scoped resources created by the operator have been changed so they all use an `educates` prefix. The name of the status key in custom resources managed by the operator has changed from `eduk8s` to `educates`. Names of service accounts and role bindings in workshop and session namespace have also changed.

So long as workshop definitions used the appropriate data variables in session and environment objects they should not be affected by these changes.

Note that the older `eduk8s` naming is still used inside of the workshop container image for the user home directory, user name etc.

### Hostnames for proxied ingresses

When configuring the workshop session to act as a proxy using `spec.session.ingresses` an ingress is automatically created. The format of the host name for the ingress is:

```
$(ingress_protocol)://$(session_namespace)-application.$(ingress_domain
```

Instead of a suffix for the application name, a prefix is now also supported, and bundled applications such as the console and editor now use the prefix convention.

```
$(ingress_protocol)://application-$(session_namespace).$(ingress_domain
```

Using a prefix is the recommended convention if you want to be able to create workshops that target deployment as a container using `docker` in conjunction with a `nip.io` style address.

### Stripped down workshop definition

Previously the complete `Workshop` definition was mounted into the workshop container. This is no longer the case and only a stripped down version is now provided to the workshop container. This consists of the `spec.session.applications`, `spec.session.ingresses` and `spec.session.dashboards` configuration only. This is being done to avoid sensitive information such as credentials defined in `spec.session.objects`, `spec.environment.objects` or `spec.session.patches` being visible to workshop users.
### Short names for workshop images

The only short names for workshop images that are now recognised in ``spec.content.image`` of the ``Workshop`` definition are:

* ``base-environment:*`` - A tagged version of the ``base-environment`` workshop image which has been matched with the current version of the Educates operator.
* ``jdk8-environment:*`` - A tagged version of the ``jdk8-environment`` workshop image which has been matched with the current version of the Educates operator.
* ``jdk11-environment:*`` - A tagged version of the ``jdk11-environment`` workshop image which has been matched with the current version of the Educates operator.
* ``conda-environment:*`` - A tagged version of the ``conda-environment`` workshop image which has been matched with the current version of the Educates operator.

Prior short names with `master` and `develop` tags are no longer recognised.

If necessary you can still define your own short names in a named system profile.

### Third party software upgrades

Versions of third party packages used by Educates were updated to latest available at the time. This includes Carvel tools, Kubernetes dashboard, `kustomize`, `helm`, `skaffold` etc. The `kubectl` versions currently provided are 1.20 through 1.23.

### Upgrade of VS Code version

Educates was updated to use the latest major update of VS Code package from [Coder](https://github.com/coder/code-server). This is version v4.x vs the previously used v3.x version.

Due to changes in how the newer version of VS Code handles extensions, Educates no longer installs any editor extensions by default. It is therefore up to a specific workshop to install the editor extensions they want to use.

Installation of editor extensions can be done from a `workshop/setup.d` file when the workshop container starts.

You can either directly install the extension from the [Open VSX Registry](https://open-vsx.org/), or bundle the `vsix` file with the workshop assets and install it from the local file system

If for example you were running a Java workshop, you might include an executable setup script file in `workshop/setup.d` containing:

```
#!/bin/bash

set +x

code-server --install-extension Pivotal.vscode-spring-boot@1.30.0
code-server --install-extension redhat.java@1.3.0
code-server --install-extension vscjava.vscode-java-debug@0.38.0
code-server --install-extension vscjava.vscode-java-dependency@0.19.0
code-server --install-extension vscjava.vscode-java-test@0.34.1
code-server --install-extension vscjava.vscode-maven@0.35.0
code-server --install-extension vscjava.vscode-spring-initializr@0.8.0
```

Note that the path to `code-server` also changed with this update to `/opt/editor/bin/code-server`. Previously it was `/opt/code-server/bin/code-server`.

If you didn't want to automate installation of extensions, you could just instruct a user to install the extension themselves via the VS Code interface as part of the workshop instructions.

Note that one of the reasons that editor extensions are no longer installed by default is because some extensions have significant memory resource requirements even when not being used. This is the case for the Java extension. You should therefore only install an editor extension if you absolutely need it and it is used by the workshop.

### OpenShift client and console

Client tools for working with OpenShift, including support for the OpenShift web console were removed.

### Secretgen controller blocking

Because of the inherit security risks in how Carvel Secretgen Controller works, it is now blocked from copying secrets into any Educates namespaces using a wildcard for the destination namespace. This is done to stop sensitive credentials held in image pull secrets being copied into session namespaces where an untrusted user can access them and use them to access services they shouldn't. If you legitimately need the ability to copy secrets into all session namespaces for a workshop, the builtin secret copier provided with Educates is a better option as it provides more flexibility around which namespaces a secret should be copied to.

### Logging of workshop downloads

When workshop content is being download, the output of the download script is now saved in `$HOME/.eduk8s/download-workshop.log` so the reasons for failure can be worked out from the workshop terminal, rather than needing to look at the workshop container pod logs.

New Features
------------

### Workshop analytics events

A clickable action in the workshop instructions can be designated as an event source for analytics delivered by the analytics webhook defined for a training portal. Additional events are now also generated for a workshop session being created (distinct from a workshop session being started), as well as creation, termination and deletion of workshop environments, creation and deletion of anonymous user accounts, plus events for errors such as failure to download workshop content or run setup scripts. Events will also be generated for deletion of workshop sessions which had never been allocated to users. For more information see:

* [Generating events for actions](generating-events-for-actions)
* [Collecting analytics on workshops](collecting-analytics-on-workshops)

### Clickable actions in Javascript

The functionality of a subset of clickable actions can be accessed from web pages or web sites embedded in a dashboard tab, using Javascript messages. For more information see:

* [Triggering actions from Javascript](triggering-actions-from-javascript)

### Disabling ingress authentication

When specifying additional ingress points, by default access to the URL will be protected by the workshop session access controls. To disable the access controls on the URL it is now possible to override the authentication type. For more information see:

* [Defining additional ingress points](defining-additional-ingress-points)

### Downloading of workshop content

Downloading of workshop content by specifying `spec.content.files` has been deprecated and is replaced with `spec.content.downloads`. This new mechanism uses `vendir` under the covers to download workshop content from one or more sources. For more information see:

* [Downloading workshop content](downloading-workshop-content)
