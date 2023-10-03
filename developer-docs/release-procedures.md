Release Procedures
==================

All changes pertaining to a new release should be worked on in forks of the main Educates GitHub repository, with changes submited via pull requests back to the `develop` branch of the main repository. When it is time for a release, the following steps should be followed.

Updates to the Documentation
----------------------------

Before any release is performed, documentation should first be updated for any changes being made in the release. Documentation updates should consist of:

* Additions or updates to core documentation related to any new features or changes.
* Addition of release notes for the release. This should be added to the [project-docs/release-notes](../project-docs/release-notes) directory.
* Link the release notes into the documentation table of contents. This should be added to [project-docs/index.rst](../project-docs/index.rst).
* Update the notice for the current released version of Educates. This should be added to [project-docs/project-details/project-overview.md](../project-docs/project-details/project-overview.md).

Where changes are non trivial or need further explaination, the release notes should include a cross reference to other parts of the documentation describing the feature.
