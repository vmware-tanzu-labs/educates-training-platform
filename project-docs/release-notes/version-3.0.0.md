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

Bugs Fixed
----------

* A workshop environment could technically get stuck in `STARTING` state as seen
  by the training portal if the kopf operator framework coalesced events for
  `ADDED` and `MODIFIED` together and only reported a single `ADDED` event. This
  is because the training portal was only looking for a `MODIFIED` event. Thus
  it could miss when the workshop details were updated in `WorkshopEnvironment`
  and so not mark the workshop environment as `RUNNING`.
