Learning Center
===============

The Learning Center platform integrated into the Tanzu Application Platform was a fork of Educates 1.X taken at the beginning of 2021.

Some modifications were made to Educates 1.X when it was integrated into Tanzu Application Platform as Learning Center, which means that workshops cannot be migrated between the two without changes. The following lists some of the known incompatibilities between the two platforms resulting from changes made in Learning Center, and Educates since that time. You should also consult the release notes for each version of Educates to learn what new features have been added, or what other changes have been made.

Note that although some of the old methods for configuring Learning Center still work due to backward compatibility support, you should not rely on that working as such support will be removed in a future release. You should therefore aim to migrate any configuration to the newer configuration layout.

Training platform deployment
----------------------------

The installation process for both Learning Center and Educates both involve using a Carvel package to facilitate installation, however due to Learning Center having been a part of Tanzu Application Platform, the overall process is somewhat different.

Educates now also provides an ``educates`` CLI which can be used to deploy a local instance of a Kubernetes cluster using Kind, with Educates installed.

For exact details on how to install Educates consult the installation instructions for Educates.

Kubernetes resource versions
----------------------------

The API group name and version for Kubernetes resources used to describe and deploy workshops in Learning Center is different to those used in Educates.

In the case of Learning Center the API group name is ``learningcenter.tanzu.vmware.com`` where as in Educates it is ``training.educates.dev``. Thus in the case of a ``Workshop`` definition, you would need to change it from:

```
apiVersion: learningcenter.tanzu.vmware.com/v1beta1
kind: Workshop
```

to:

```
apiVersion: training.educates.dev/v1beta1
kind: Workshop
```

In both cases the API version is ``v1beta1``.

This change is also required for the ``TrainingPortal`` resource.

Although not normally used directly, the API group name has similarly changed for ``WorkshopSession`` and ``WorkshopEnvironment``.

If you had previously use the ``learningcenter`` or ``learningcenter-training`` resource category aliases to list resources with ``kubectl``, you will now need to use ``educates`` or ``educates-training``.

```
kubectl get educates
```

This will list instances of all the Educates custom resource types in the specified scope.

Where needing to provide the full name of a custom resource when querying it, to disambiguate it from resources of the same name used by other packages, such as that for ``Workshop`` definitions, you would now need to use:

```
kubectl get workshops.training.educates.dev
```

Workshop base image specification
---------------------------------

In Learning Center, when a workshop required a custom workshop base image it would be specified in the ``Workshop`` definition as:

```yaml
spec:
  content:
    image: ghcr.io/{organization}/{image}:latest
```

In Educates the location for the ``image`` property has changed and you should instead use:

```yaml
spec:
  workshop:
    image: ghcr.io/{organization}/{image}:latest
```

Note that whereas Learning Center only bundled a single workshop base image, Educates provides a number of options. These can be selected using the following image references.

``base-environment:*`` - A tagged version of the ``base-environment`` workshop image which has been matched with the current version of the Educates operator.

``jdk8-environment:*`` - A tagged version of the ``jdk8-environment`` workshop image which has been matched with the current version of the Educates operator.

``jdk11-environment:*`` - A tagged version of the ``jdk11-environment`` workshop image which has been matched with the current version of the Educates operator.

``jdk17-environment:*`` - A tagged version of the ``jdk17-environment`` workshop image which has been matched with the current version of the Educates operator.

``jdk21-environment:*`` - A tagged version of the ``jdk21-environment`` workshop image which has been matched with the current version of the Educates operator.

``conda-environment:*`` - A tagged version of the ``conda-environment`` workshop image which has been matched with the current version of the Educates operator.

Downloading of workshop content
-------------------------------

Learning Center supported downloading workshop content from a hosted Git repository on GitHub or Gitlab, a HTTP server, or as an OCI image. Educates still supports these, but also supports a range of new options.

In Learning Center, configuration in the ``Workshop`` definition for downloading workshop content consisted of an entry such as:

```yaml
spec:
  content:
    files: github.com/{organization}/{repository}
```

This entry is now replaced with a new format, where a configuration snippet for ``vendir`` is instead supplied.

For the case of downloading workshop content hosted on GitHub you now need to use:

```yaml
spec:
  workshop:
    files:
    - git:
        url: https://github.com/{organization}/{repository}
        ref: origin/main
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

Note that the ``.eduk8signore`` file is only relevant to old ``workshop.content`` mechanism. In the new mechanism using ``vendir`` you should use ``includePaths`` and ``excludePaths`` in the workshop definition to filter what is included or excluded.

For the case of downloading workshop content hosted on a HTTP server you now need to use:

```yaml
spec:
  workshop:
    files:
    - http:
        url: https://{hostname}/workshop.tgz
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

And for workshop content hosted as an OCI image artifact on an image registry:

```yaml
spec:
  workshop:
    files:
    - image:
        url: $(image_repository)/{name}-files:latest
      includePaths:
      - /workshop/**
      - /exercises/**
      - /README.md
```

Note that where as in Learning Center if credentials were required they needed to be supplied in the URI reference, in Educates these need to be provided via a secret and a secret reference supplied in the ``vendir`` configuration snippet.

For more details consult the Educates documentation and also the ``vendir`` documentation.

Cluster security policy names
-----------------------------

For any workshop which is deployed it can dictate what security policy is applied to it. This security policy dictates what sort of actions a workshop user can make against namespaces in the Kubernetes cluster they have access to. The names of these security policies have been changed to align with more recent naming conventions used by Kubernetes. Where this configuration is placed in the ``Workshop`` definition has also changed.

In Learning Center the security policy was defined by providing in the ``Workshop`` definition:

```yaml
spec:
  session:
    security:
      policy: anyuid
```

The possible values for the ``policy`` property were ``nonroot``, ``anyuid`` and ``custom``.

In Educates the security policy should be defined in the ``Workshop`` definition as:

```yaml
spec:
  session:
    namespaces:
      security:
        policy: baseline
```

The equivalent security policy names are:

| Learning Center | Educates   |
|-----------------|------------|
| nonroot         | restricted |
| anyuid          | baseline   |
| custom          | privileged |

The access provided for each security policy is similar to what is provided by Kubernetes pod security standards.

If a desired security policy is not specified then it will default to ``restricted``.

You should avoid using ``privileged`` on any workshop which would be undertaken by untrusted users.

Resorce quota memory limits
---------------------------

Resource quotas and limit ranges are applied to any Kubernetes namespaces associated with a workshop session. In the case of memory, in Learning Center the limit ranges were set, depending on the budget selected, as:

```text
| Budget    | Min  | Max  | Request | Limit |
|-----------|------|------|---------|-------|
| small     | 32Mi | 1Gi  | 128Mi   | 256Mi |
| medium    | 32Mi | 2Gi  | 128Mi   | 512Mi |
| large     | 32Mi | 4Gi  | 128Mi   | 1Gi   |
| x-large   | 32Mi | 8Gi  | 128Mi   | 2Gi   |
| xx-large  | 32Mi | 12Gi | 128Mi   | 2Gi   |
| xxx-large | 32Mi | 16Gi | 128Mi   | 2Gi   |
```

These default limit ranges in Educates have been changed to:

```text
| Budget    | Min  | Max  | Request | Limit |
|-----------|------|------|---------|-------|
| small     | 1M   | 1Gi  | 128Mi   | 256Mi |
| medium    | 1M   | 2Gi  | 128Mi   | 512Mi |
| large     | 1M   | 4Gi  | 128Mi   | 512Mi |
| x-large   | 1M   | 8Gi  | 128Mi   | 512Mi |
| xx-large  | 1M   | 12Gi | 128Mi   | 512Mi |
| xxx-large | 1M   | 16Gi | 128Mi   | 512Mi |
```

As the default upper limit has been reduced, you may need to ensure any deployments created from a workshop session properly indicate what resources they require, or you will instead need to override the default limit range values.

Hostnames for proxied ingresses
-------------------------------

In a ``Workshop`` defintion it is possible to specify a list of additional ingresses that should be created for accessing services via the workshop session.

```yaml
spec:
  session:
    ingresses:
    - name: application
      port: 8080
```

In Learning Center the convention was that the hostname created would be of the form:

```
$(session_namespace)-application.$(ingress_domain)
```

Although this old convention is still supported, Educates now instead uses a prefix instead of a suffix.

Note that you should also now use ``$(session_name)`` instead of ``$(session_namespace)`` unless you need to refer to the name of the Kubernetes namespace associated with a workshop session which has access to the Kubernetes cluster. So in this case what should be used is:

```
application-$(session_name).$(ingress_domain)
```

Use of a prefix for the ingress name is recommended as DNS services such as ``nip.io`` have special support for such a prefix when using a hostname like:

```
application-A-B-C-D.domain
```

where ``A-B-C-D`` is used to represent an IP address of ``A.B.C.D``.

If the prefix convention is followed then where a workshop supports it, it can be deployed to a local Docker instance to provide a workshop rather than requiring a full Educates installation.

Session environment variables
-----------------------------

In order for a workshop to dynamically set environment variables which are then available to the workshop dashboard terminals, it is possible to supply ``profile.d`` scripts with the workshop files. This feature still exists, but will likely be deprecated and removed at some point in the future.

If a workshop needs to set environment variables, use the new feature of ``setup.d`` scripts where they can write out any environment variables that need to be set, to the ``.env`` file specified by the ``WORKSHOP_ENV`` environment variable in the ``setup.d`` script.

Restrictions on ingress hostnames
---------------------------------

In Learning Center when creating a Kubernetes ingress, either explicitly via the configuration of the workshop session, or by actions of the workshop user, any hostname could be used for the ingress. This meant a workshop user could create ingresses which interfered with other workshops users or other applications deployed to the Kubernetes cluster.

In Educates, rules enforced by the Kyverno security policy engine which is enabled for workshops, mean that an ingress created against a workshop session must include the unique session name in it or creation of the ingress will be blocked. Any hostname used in an ingress must therefore be of the form:

```
prefix-$(session_name).$(ingress_domain)
```

or:

```
$(session_name)-suffix.$(ingress_domain)
```

No editor extensions by default
-------------------------------

When the embedded VS Code editor was enabled, Learning Center would pre-install a number of editor extensions. When using Educates it no longer installs any editor extensions by default. It is therefore up to a specific workshop to install the editor extensions they want to use.

Installation of editor extensions can be done from a ``workshop/setup.d`` file when the workshop container starts.

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

Note that the path to ``code-server`` also changed with this update to ``/opt/editor/bin/code-server``. Previously it was ``/opt/code-server/bin/code-server``. It is now however included in `PATH` and so you shouldn't need to use the absolute pathname.

If you didn't want to automate installation of extensions, you could just instruct a user to install the extension themselves via the VS Code interface as part of the workshop instructions.

Note that one of the reasons that editor extensions are no longer installed by default is because some extensions have significant memory resource requirements even when not being used. This is the case for the Java extension. You should therefore only install an editor extension if you absolutely need it and it is used by the workshop.

Workshop instructions renderer
------------------------------

In Learning Center workshop instructions could be provided as either Markdown or AsciiDoc. These were rendered using a custom HTML renderer implemented as part of the platform. In Educates this is referred to as the "classic" renderer for workshop instructions.

Although the classic renderer is still supported at this time, Educates has added support for using the Hugo static site generator for rendering workshop instructions. It is expected that in time the older classic renderer will be retired and all workshop instructions will need to use the Hugo based renderer for workshop instructions. You should therefore investigate converting the format of workshop instructions. See the separate documentation on migrating from the classic renderer to the Hugo based renderer.

Portal default workshop settings
--------------------------------

In Learning Center, default settings could be specified for any workshops listed in the ``TrainingPortal`` resource using:

```yaml
spec:
  portal:
    sessions:
      maximum: 10
    capacity: 6
    reserved: 2
    initial: 4
  workshops:
  - name: lab-asciidoc-sample
  - name: lab-markdown-sample
```

The values for ``capacity``, ``reserved`` and ``initial`` properties would be inherited by any workshop listed which didn't override these values.

In Educates the placement of these default values has changed and you should now use:

```yaml
spec:
  portal:
    sessions:
      maximum: 10
    workshop:
      defaults:
        capacity: 6
        reserved: 2
        initial: 4
  workshops:
  - name: lab-asciidoc-sample
  - name: lab-markdown-sample
```

User interface style overrides
------------------------------

Learning Center replaced the existing user interface implementation resulting in changes to the element structure of the the training portal, workshop dashboard and workshop renderer. As a result, any style overrides originally designed for Educates will not work with Learning Center, and vice versa. The manner in which style overrides is provided in Educates is also now quite different due to the elimination of the ``SystemProfile`` custom resource. For more details consult the configuration settings documentation for Educates.
