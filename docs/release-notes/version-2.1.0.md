Version 2.1.0
=============

New Features
------------

* Added ability to source workshop content from a local directory in the
  workshop container. This was added to permit workshop content to be taken
  from a mounted volume. This could be a persistent volume preloaded with the
  workshop content as part of the workshop environment, or could be a
  preclaimed volume mapping to host file system, the latter permitting the
  injection of workshop content from a local host when using a Kind cluster.

* Add means to override the image registry in the `TrainingPortal`, which would
  be used when interpolating `$(image_repository)` in the `Workshop` definition
  settings for the workshop image and content.

* Generate analytic events from the session manager when `TrainingPortal`,
  `WorkshopEnvironment` and `WorkshopSession` are being processed. Note that
  these are only reported when webhook URL for reporting events is provided
  in global configuration and not when only specified via `TrainingPortal`.

* The workshop container home directory is now shared with the `dockerd` side
  car container when `docker` support is enabled for a session. This means that
  any containers started using docker can mount the workshop container home
  directory if required to access workshop files.

* Added `docker-compose` CLI extension for `docker` to the workshop base image.

* Added ability to specify services that should be started automatically when
  `docker` support is enabled for a session. Such services need to be specified
  using `docker compose` configuration within the workshop definition. For more
  information see [Enabling ability to use docker](enabling-ability-to-use-docker).

* It is now possible to specify the Kubernetes version to be deployed when using
  a virtual cluster. For more information see
  [Provisioning a virtual cluster](provisioning-a-virtual-cluster).

Features Changed
----------------

* Improvements to how status of deployment for training portal, workshop
  environment and workshop session are tracked in custom resources, with the
  details of any errors added via a status message.

* Experimental code related to running `dockerd` in rootless and unprivileged
  modes removed as never function correctly, in part because require kernel
  used on nodes to be configured in a specific manner.

* Update `kubectl` versions available so can support Kubernetes 1.20-1.25.

* The workshop image now uses port 10081 instead of port 10080 for the inbound
  gateway process for the workshop dashboard. Any custom workshop images will
  need to be rebuilt against latest workshop base image. This change should
  make no difference when hosting workshops in Kubernetes, but will effect
  any use case where workshop image was being used directly in local docker.

* Changed convention for default ingress domain when running workshop image
  directly in local docker. Now uses `127-0-0-1.nip.io` instead of using
  `127.0.0.1.nip.io`.

Bugs Fixed
----------

* Although only Intel versions of images are provided, should now work on ARM
  based macOS in emulation mode.

* When waiting for `ResourceQuota` to be ready, check for `used` status value
  as well as `hard`. This was to avoid timing issue when using OpenShift where
  updates to `used` status value were slower and not waiting could result in
  subsequent error when creating resources subject to quota on the number of
  that resource type.

* Change handling of cover pages to avoid white page being flashed between
  cover pages presented by training portal and workshop dashboard.

* Fix button to dismiss cover page for workshop dashboard and automatically
  remove it after a period of time when workshop setup taking too long.

* Fix issues with removing/adding workshops directly from `TrainingPortal`
  instance where the corresponding `Workshop` definition was missing. This was
  resulting in any changes to set of workshop being ignored due to errors.

* Training portal would fail to reconcile list of workshops if the list of
  workshops was set to be an empty list.
