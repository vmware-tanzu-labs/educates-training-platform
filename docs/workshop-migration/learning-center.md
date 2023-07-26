Learning Center
===============

The Learning Center platform integrated into the Tanzu Application Platform was a fork of Educates 1.X taken at the beginning of 2021.

Some modifications were made to Educates 1.X when it was integrated in Tanzu Application Platform as Learning Center, which means that workshops cannot be migrated between them without changes. The following lists some of the known incompatibilities between the two platforms resulting from changes made in Learning Center.

Kubernetes resource versions
----------------------------

The api group name and version for Kubernetes resources used to describe and deploy workshops was changed in Learning Center.

User interface style overrides
------------------------------

Learning Center replaced the existing user interface implementation resulting in changes to the element structure of the the training portal, workshop dashboard and workshop renderer. As a result, any style overrides originally designed for Educates will not work with Learning Center, and vice versa.
