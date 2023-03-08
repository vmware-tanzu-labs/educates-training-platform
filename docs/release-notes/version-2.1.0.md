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
  a virtual cluster, as well as provide a list of raw Kubernetes resource objects
  that should be added to the cluster when created. For more information see
  [Provisioning a virtual cluster](provisioning-a-virtual-cluster).

* Added option to specify the runtime class for workshop pods. This is set in
  the global configuration when Educates is installed and makes it possible to
  force workshop containers to run in Kata containers for extra security. For
  more information see
  [Overriding container runtime class](overriding-container-runtime-class).

* A random password token for use with arbitrary services deployed along with a
  workshop is now provided. The name of the data variable for use in the
  workshop definition and workshop instructions is `services_password`. The
  name of the environment variable accessable within the workshop container is
  `SERVICES_PASSWORD`.

* An SSH key pair is now generated for each workshop session. The value of each
  component of the SSH key pair are made available as a secret and variables
  in the workshop definition. They are also injected into the workshop container
  and placed into `$HOME/.ssh` directory.

* In addition to being able to set environment variables for a workshop session
  using `profile.d` scripts included with workshop content, it is now possible
  from a `setup.d` file to output a list of the environment variables to be set
  by writing then to a `.env` file the name of which is given by the
  `WORKSHOP_ENV` environment variable available to the `setup.d` script.

* Added support for syntax highlighting of fenced code blocks in markdown
  version of workshop instructions.

* Added REST API endpoint to training portal for terminating a workshop.

* Added stop button to top right of initial splash screen when workshop
  dashboard is accessed. If during initial workshop session creation a failure
  occurs and the browser is stuck on the splash screen, the stop button can be
  pressed and the workshop session will be deleted and the browser redirected
  back to the training portal or other configured workshop portal.

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

* Access to Kubernetes network policies in the workshop session namespaces are
  now blocked from the workshop user so they cannot find out which IP addresses
  they are being blocked from accessing.

* Minimum value for memory limit ranges changed from 1Mi to 1M as metric unit is
  smaller than SI unit.

* When using the version of Contour bundled with Educates, HTTP/2 is disabled
  on the ingress router so that macOS/iOS Safari (Webkit) browser will work more
  reliably for accessing workshop sessions. If installing Educates into a
  cluster where an ingress router already exists, you would need to separately
  configure it to disable HTTP/2 if required.

* When using the REST API of the training portal, a robot account can now
  extend or terminate running workshop sessions.

* When overriding the source for workshop instructions, replacing it with an
  alternate web application process running in the workshop container, the
  new provider of the workshop instructions can now use web sockets.

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
