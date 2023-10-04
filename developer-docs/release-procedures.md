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

Where changes are non trivial or need further explanation, the release notes should include a cross reference to other parts of the documentation describing the feature.

Triggering a Development Build
------------------------------

For any individual code changes the developer of the changes should have already built and tested the changes on their local system. If a complete build of Educates consisting of all code changes for a release is required, a build from the `develop` branch can be triggered using a GitHub actions workflow dispatch trigger event. This can be done from the GitHub actions page of the main Educates GitHub repository located at:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/actions](https://github.com/vmware-tanzu-labs/educates-training-platform/actions)

![](github-actions-build.png)

From the GitHub actions page select "Build and Publish Images" from the list of workflows, then click on the "Run workshop" dropdown. In the drop down select the branch `develop` and then the list of platforms to run the build.

By default the build will only be run for the `linux/amd64` platform. The `linux/arm64` platform can instead be selected, or both, by selecting `linux/amd64,linux/arm64`. Note that any `linux/arm64` build will take significantly longer as the build is done under GitHub actions using the QEMU machine emulator and virtualizer.

Being a development build, all the container images, client programs and package bundles will be created, but neither a package repository bundle or GitHub release will be created. To test the release, clients programs and package resource manifests for installing the development version can be downloaded from the build artifacts of the GitHub actions workflow run. Client programs can also be download by using the command:

```
imgpkg pull -i ghcr.io/vmware-tanzu-labs/educates-client-programs:develop -o /tmp/client-programs
```

A development build prior to a release would be done against the main Educates GitHub repository. If necessary a developer of some changes could also trigger such a build using GitHub actions from their fork of the Educates GitHub repository. In this case all container image references will resolve to images built and pushed to the developers GitHub container registry namespace and not that of the main Educates GitHub repository. For more complicated changes, it possibly should be a requirement that a developer do a full development build from their fork and test it before creating a pull request with their changes.

Tagged Pre-release Versions
---------------------------

Development builds created by manually invoking the GitHub actions workflow are mutable and would be replaced by a subsequent development build. If you want to generate a more official pre-release version for testing (alpha, beta, or release candidate), you can create a tag in the Git repository against the corresponding commit in the `develop` branch and push the tag to GitHub. Pushing the tag will automatically trigger the GitHub action workflow to run. As with a development build all the container images, client programs and package bundles will be created. This time a GitHub release will be also be created but marked as pre-release. A package repository will still not be created however.

The format of the tags you can use for pre-release builds are:

* `X.Y.Z.alpha-N`
* `X.Y.Z.beta-N`
* `X.Y.Z.rc-N`

These can be created against a branch of a fork created from the main GitHub repository, in which case the release will be added against the fork and not the main GitHub repository.

Because the same tag might be used in the main GitHub repository, which would be propagated to the fork when the repositories are synchronized, use of these tags is discouraged in forks except for testing release procedures. If done for this purpose, it is suggest that a tag of the form `0.0.1.???-N` be used, and that after testing both the tag and GitHub release be deleted once no longer required, so that the same tag can be used again in such future testing.  
