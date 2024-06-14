Version 3.0.0
=============

Upcoming Changes
----------------

For details on significant changes in future versions, including feature
deprecations and removals which may necessitate updates to existing workshops,
see [Upcoming changes](upcoming-changes).

Features Changed
----------------

* When using `educates create-cluster`, if you want the local secrets cache to
  be copied to the cluster and the installation configuration to be
  automatically adjusted to use the wildcard certificate or CA secrets, you must
  supply the `--with-local-secrets` option.

* The `educates admin platform update` command no longer exists for when using
  local user config with `educates create-cluster`. If you want to update the
  in-cluster configuration for Educates when using the local user config, you
  will need to output the config to a separate file and use `educates admin
  platform deploy`.

  ```
  educates admin config edit
  educates admin config view > config.yaml
  educates admin platform deploy --config config.yaml
  ```
