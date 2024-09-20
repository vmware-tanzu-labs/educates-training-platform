Version 3.0.1
=============

Upcoming Changes
----------------

For details on significant changes in future versions, including feature
deprecations and removals which may necessitate updates to existing workshops,
see [Upcoming changes](upcoming-changes).

New Features
------------

* Added opinionated installer configuration for Minikube. Will by default
  install Contour as the ingress controller, but can be disabled if using the
  nginx ingress controller provided by Minikube.

Features Changed
----------------

* When requesting a workshop session using the lookup service, a search for an
  existing session for that workshop and user is now made against all training
  portals across all clusters. This is done before filtering out what training
  portals are accessible to a tenant. This is done so an existing workshop
  session is found even if labels for clusters or portals had been changed such
  that the training portal is no longer mapped to the tenant. Such changes to
  labels may have been made to prevent creation of new workshop sessions against
  a cluster or training portal when rolling over to a new cluster and waiting
  for existing workshop sessions on the old cluster to expire. Note that this
  relies on client side user IDs to be unique across all tenants hosted by the
  clusters the lookup service monitors. If a single lookup service is being used
  by multiple distinct custom front end web portals and it is possible the same
  user ID could be used by more than one front end, it is recommended that the
  front end incorporate the tenant name as part of the client side user ID
  passed to the lookup service.

Bugs Fixed
----------

* When the `kind` infastructure provider was selected for the opinionated
  installer, if a CA certificate was provided and installation of `educates`
  training platform component was being disabled, the latter was still being
  installed even though disabled.

* If a locally managed config file had not been created using the command
  `educates local config edit` prior to running `educates create-cluster`, it
  would fail as the local config directory wasn't being created automatically.

* Using the `custom` provider when the `educates` component was enabled, would
  fail when using CLI to create or update a cluster as image references were not
  being replaced with references to where released image artifacts were stored.
