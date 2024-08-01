Version 3.0.0
=============

Upcoming Changes
----------------

For details on significant changes in future versions, including feature
deprecations and removals which may necessitate updates to existing workshops,
see [Upcoming changes](upcoming-changes).

New Features
------------

* New data variable added for `registry_auth_token`. This combines both the
  registry username and password, separated by a colon, and base64 encoded. The
  format is as would be expected for HTTP Basic authentication. The variable can
  be used when setting headers for a session ingress proxy. This is also
  available as an environment variable in a workshop session as the variable
  `REGISTRY_AUTH_TOKEN`.

* New data variable added for `git_auth_token`. This combines both the Git
  username and password, separated by a colon, and base64 encoded. The format is
  as would be expected for HTTP Basic authentication. The variable can be used
  when setting headers for a session ingress proxy. This is also available as an
  environment variable in a workshop session as the variable `GIT_AUTH_TOKEN`.

* The identifier for the user to which a workshop session is allocated is now
  recorded in the status of the `WorkshopSession` resource, as well as in the
  `WorkshopAllocation` resource.

Features Changed
----------------

* Installation of Educates to an existing Kubernetes cluster using Carvel
  `PackageRespository` mechanism has been removed. Simpler mechanism using
  Carvel `App` resource should now be used. See [Installation
  instructions](installation-instructions) for updated details.

* Installation of Educates to an existing Kubernetes cluster is now easier using
  the Educates CLI.  See [Installation instructions](installation-instructions)
  for updated details.

* The `educates admin config` group of commands is now accessible using
  `educates local config`.

* The `educates admin secrets` group of commands is now accessible using
  `educates local secrets`.

* The `educates admin registry` group of commands is now accessible using
  `educates local registry`.

* The `educates admin resolver` group of commands is now accessible using
  `educates local resolver`.

* The `educates admin platform update` command no longer exists for when using
  local user config with `educates create-cluster`. If you want to update the
  in-cluster configuration for Educates when using the local user config, you
  will need to run `educates admin platform deploy` command and supply the
  `--local-config` option.

  ```
  educates local config edit
  educates admin platform deploy --local-config
  ```

* Installation of an ingress controller inside of a virtual cluster is no
  longer dependent on having `kapp-controller` installed on the underlying
  host cluster.

* When the orphaned timeout is specified for a workshop in the training portal,
  if the browser page has been closed for that period of time the workshop
  session will be terminated. In addition to this behaviour when the orphaned
  timeout is specified, if a browser page/tab is hidden for a period of 3 times
  the orphaned timeout, indicating that the workshop user is not interacting
  with the workshop session, the workshop session will now also be terminated.
  Thus if the orphaned timeout had been set to 5 minutes, the workshop session
  where the browser page had been hidden/inactive for 15 minutes will be
  terminated. Note that what constitutes hidden may depend on the web browser.
  For example, a browser may not mark the page as hidden if the browser page is
  not full screen and is merely covered by another window from the same
  workspace. Do note that for supervised workshops where the whole event only
  lasts a certain amount of time, you should avoid the orphaned timeout setting
  so that a users session is not deleted when they take breaks and their
  computer goes to sleep.

Bugs Fixed
----------

* Theme overrides were not being applied to access control pages of the
  training portal.

* The `changeOrigin` property was missing from the `Workshop` custom resource
  defintion for `ingresses` even though was documented as something that could
  be set.

* The `educates local config edit` command would fail if run prior to having
  ever created a local Educates cluster as the config directory would not exist.

* Fixes a timing issue where the `phase` recorded against a `WorkshopSession`
  resource created by a training portal, would revert to `Available` rather than
  being set to be `Allocated`.

* An attempt to reacquire a workshop session for a user via the REST API which
  had not been created via the REST API but by the web interface would result in
  an internal error. Now properly disallow the request for this case and return
  an error saying session cannot be reacquired.
