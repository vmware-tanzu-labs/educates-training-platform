Learning Center
===============

The Learning Center platform integrated into the Tanzu Application Platform was a fork of Educates 1.X taken at the beginning of 2021.

Some modifications were made to Educates 1.X when it was integrated in Tanzu Application Platform as Learning Center, which means that workshops cannot be migrated between the two without changes. The following lists some of the known incompatibilities between the two platforms resulting from changes made in Learning Center, and Educates since that time. You should also consult the release notes for each version of Educates to learn what new features have been added, or what other changes have been made.

Training platform deployment
----------------------------

The installation process for both Learning Center and Educates both involve using a Carvel package to facilitate installation, however due to Learning Center having been a part of Tanzu Application Platform, the overall process is somewhat different and Educates has done away with the ``SystemProfile`` custom resource type.

For Educates there is also now an ``educates`` CLI which can be used to deploy a local instance of a Kubernetes cluster using Kind, with Educates installed.

For exact details on how to install Educates consult the installation instructions for Educates.

Kubernetes resource versions
----------------------------

The api group name and version for Kubernetes resources used to describe and deploy workshops in Learning Center is different to those used in Educates.

In the case of Learning Center the API group name is ``learningcenter.tanzu.vmware.com`` where as in Educates 2.X it is ``training.educates.dev``. Thus in the case of a ``Workshop`` definition, you would need to change it from:

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

The values for ``capacity``, ``reserved`` and ``initial`` properties would be inherited any any workshop listed which didn't override these values.

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

```
application-$(session_namespace).$(ingress_domain)
```

Use of a prefix for the ingress name is recommended as DNS services such as ``nip.io`` have special support for such a prefix when using a hostname like:

```
application-A-B-C-D.domain
```

where ``A-B-C-D`` is used to represent an IP address of ``A.B.C.D``.

If the prefix convention is followed then where a workshop supports it, it can be deployed to a local Docker instance to provide a workshop rather than requiring a full Educates installation.

User interface style overrides
------------------------------

Learning Center replaced the existing user interface implementation resulting in changes to the element structure of the the training portal, workshop dashboard and workshop renderer. As a result, any style overrides originally designed for Educates will not work with Learning Center, and vice versa. The manner in which style overrides is provided in Educates is also now quite different due to the elimination of the ``SystemProfile`` custom resource. For more details consult the configuration settings documentation for Educates.
