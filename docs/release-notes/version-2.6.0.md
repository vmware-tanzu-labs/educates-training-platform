Version 2.6.0
=============

New Features
------------

* Add option for having workshop instructions rendered using Hugo. This mode
  will be automatically used if neither of the files `workshop/workshop.yaml` or
  `workshop/modules.yaml` used by the original workshop renderer exist. The
  Markdown files for the workshop instructions should still reside in the
  directory `workshop/content`. By default page ordering for instructions will
  be based on the sorted order of the page filenames. If any page contains
  metadata specifying a page weight, then default Hugo page ordering will be
  applied instead using page weight and page title. In either case, the page
  title can be specified in the page metadata. Where necessary a
  `workshop/config.yaml` file can optionally be supplied when Hugo rendering
  mode is used. This file can be used to specify additional page variables to be
  available when doing page rendering, as well as explicitly define one or more
  navigation pathways through the workshop instructions. Hugo shortcodes are
  provided for optionally including parts of instructions based on the pathway
  being used, as well as shortcodes for admonitions. Clickable actions still
  work by using fenced code blocks, as was done using the original workshop
  renderer.

* Added new variation for how remotely hosted workshop instructions can be used
  with a workshop session, where instead of the iframe for workshop instructions
  triggering a redirect to the remote site, an internal proxy can instead be
  configured. The result is that the embedded workshop instructions will be
  accessed from a browser using the same workshop session hostname, with the
  remote instructions being under the `/workshop/content` URL path. Because the
  workshop instructions appear under the same hostname, they can include
  Javascript which accesses the parent workshop dashboard directly, or which
  makes HTTP calls to the workshop dashboard, without encountering CORS issues.
  At the same time, the remotely hosted workshop instructions could also include
  the Javascript bundle used by the builtin workshop renderer for handling
  clickable actions. Thus if the remotely hosted workshop instructions use a
  compatible renderer for handling fenced code blocks, clickable actions can be
  used from the remotely hosted workshop instructions.

* Added an ability to download aspects of the workshop session configuration
  from a workshop session over HTTP. These are protected by the workshop session
  cookied based authentication, but a special config password can be used as
  authentication token to allow external access by other services. The config
  password is available from within the workshop session, but is also available
  via a new REST API call from the training portal. The latter allows a custom
  portal frontend to obtain the config password for a particular session and use
  it to obtain more information directly from the workshop session. The config
  information access is provided to includes the list of workshop environment
  variables, list of data variables available for interpolation in workshop
  instructions, SSH keys and Kubernetes kubeconfig file. These could be used by
  a custom portal frontend to deliver up customized workshop instructions which
  are filled out with session specific details, to inject additional data into a
  workshop session, or push images to a per session image registry.

* Added an experimental command to the `educates` CLI which allows workshop
  instructions to be rendered locally on the users machine using the Hugo
  renderer, with customized details obtained from a live workshop session. This
  can be used in conjunction with the new feature for internally proxying to
  separately hosted workshop instructions, to have workshop instructions running
  locally, but still be embedded in the workshop dashboard for a live workshop
  session. When this is being done, the local Hugo server will be configured to
  run in active reload mode, meaning the local Markdown files can be edited and
  changes will be automatically reflected in the instructions displayed in the
  dashboard for the workshop session. Right now this feature is intended as a
  half way house and it will over time be changed and improved on, until the
  point where it is more seamless, being able to be used against any Educates
  cluster installation and not just a local cluster created using the Educates
  CLI. The eventual aim is to allow for workshop files, including the workshop
  instructions, setup scripts and other exercise files, to be sourced
  automatically from the filesytem of a local machine as part of an authoring
  mode when developing new workshop content, avoiding any need to publish a
  workshop before it is able to be used.

* When requesting a workshop session via the REST API of the training portal, it
  is now possible to override the default activation timeout of 60 seconds for a
  workshop session. The purpose in allowing this is that a custom frontend
  portal could request a workshop session, setting a much larger activation
  timeout, with the frontend portal doing its own polling of the workshop
  (possibly by accessing configuration from the workshop session), or by using
  other checks, thus determine if resources required by a workshop session are
  available, such as a full Kubernetes cluster, before actually passing the URL
  to a workshop user to access. The longer activation timeout means more time is
  provided before an unclaimed workshop session is automatically deleted.

* Added new variables for use in customizing workshop instructions or for use
  from a shell environment. These are for session name, session hostname and
  session URL.

* Exposed session termination mechanism via Javascript events, so it can be
  triggered from workshop instructions embedded from a remote site by specifying
  `workshop.url` in the workshop application definition.

* Exposed ability to preview an image via a popup dialog that spans the whole
  workshop dashboard, so it can be triggered from workshop instructions embedded
  from a remote site by specifying `workshop.url` in the workshop application
  definition.

Features Changed
----------------

* How one specifies that static HTML files are to be used for workshop
  instructions has changed. The `workshop.renderer` setting of the workshop
  application introduced in 2.5.0 for this purpose is now no longer used, with
  the location of any static HTML files for the workshop instructions needing to
  be explicitly specified using the `workshop.path` section.

* When workshop instructions are supplied as static HTML files hosted inside of
  the workshop container, the static HTML must have been created with the
  assumption that the base URL path is `/workshop/content`. Previously the
  required base URL path wasn't specified and `/` was used, however this could
  result in a conflict between URL paths for the dashboard and builtin workshop
  renderer static resources.

Bugs Fixed
----------

* An attempt to view training portal information in the admin pages of the
  training portal would result in a HTTP 500 internal server error.
