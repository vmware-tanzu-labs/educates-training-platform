Learning Center
===============

The Learning Center platform integrated into the Tanzu Application Platform is a copy/fork of Educates taken at the beginning of 2021. Work on Educates was suspended at that time, but to meet the needs of Tanzu Developer Center and KubeAcademy, development work on Educates was restarted at the beginning of 2022. The development of Educates and Learning Center now run independently.

Separate modifications have been made to both Learning Center and Educates which means that workshops cannot be migrated between them without changes.

The following lists some of the known incompatibilities between the two platforms resulting from changes made in Learning Center. The list does not cover all differences as the ongoing maintainers of Educates do not have direct knowledge of the changes that have been made to Learning Center, and so can only list more obvious changes in Learning Center. You should also consult the release notes for Educates for other changes made to Educates.

Kubernetes resource versions
----------------------------

The api group name and version for Kubernetes resources used to describe and deploy workshops was changed in Learning Center.

Because of this change in Learning Center, you will need to keep two separate versions of the resources, or use `ytt` templates to dynamically generate the appropriate resource definition based on the target platform, if wishing to support using workshop content on both platforms.

User interface style overrides
------------------------------

Learning Center replaced the existing user interface implementation resulting in changes to the element structure of the the training portal, workshop dashboard and workshop renderer. As a result, any style overrides originally designed for Educates will not work with Learning Center, and vice versa.
