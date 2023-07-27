Learning Center
===============

The Learning Center platform integrated into the Tanzu Application Platform was a fork of Educates 1.X taken at the beginning of 2021.

Some modifications were made to Educates 1.X when it was integrated in Tanzu Application Platform as Learning Center, which means that workshops cannot be migrated between them without changes. The following lists some of the known incompatibilities between the two platforms resulting from changes made in Learning Center, and Educates since that time.

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

The names of the security policies which can be selected and which dictate what level of access a workshop session has to the Kubernetes cluster have been changed to align with more recent conventions used by Kubernetes.

User interface style overrides
------------------------------

Learning Center replaced the existing user interface implementation resulting in changes to the element structure of the the training portal, workshop dashboard and workshop renderer. As a result, any style overrides originally designed for Educates will not work with Learning Center, and vice versa.
