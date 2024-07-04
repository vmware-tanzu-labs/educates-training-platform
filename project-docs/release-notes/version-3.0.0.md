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

Features Changed
----------------

* When using `educates create-cluster`, if you want the local secrets cache to
  be copied to the cluster and the installation configuration to be
  automatically adjusted to use the wildcard certificate or CA secrets, you must
  supply the `--with-local-secrets` option. The same option will also need to be
  supplied with `educates admin config view` and `educates admin platform
  deploy` commands as well.

* The `educates admin platform update` command no longer exists for when using
  local user config with `educates create-cluster`. If you want to update the
  in-cluster configuration for Educates when using the local user config, you
  will need to output the config to a separate file using `educates admin config
  view` and use `educates admin platform deploy` to apply the updated local
  config to the cluster.

  ```
  educates admin config edit
  educates admin config view --with-local-secrets > config.yaml
  educates admin platform deploy --with-local-secrets --config config.yaml
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
