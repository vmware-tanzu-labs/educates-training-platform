Version 2.7.1
=============

Features Changed
----------------

* Updated VS Code to version 1.89.1.

Bugs Fixed
----------

* If a `SecretCopier` contained multiple rules and a namespace was matched by a
  rule which was in a terminating state, the attempt to create the secret in
  that namespace would fail but not be caught. This meant that any rules which
  followed that rule were not being applied on that pass and would only be
  applied some time later after the terminating namespace had finally been
  deleted. To reduce chance of this occuring, a namespace which is not in the
  active state will be skipped for matching. Also, any unexpected exception
  will be explicitly caught and logged rather than being propogated back to the
  caller.

* In the most recent Fedora base image used by workshop images the `nc` package
  was changed so as to refer to `ncat`, breaking workshops which were used to
  the `netcat` package variant being used. The `nc` alias has been reverted to
  use `netcat` by installing `netcat` package instead of `nc`. The `ncat`
  package is also installed if want newer variant of `nc`, but you will need to
  use the `ncat` command explicitly.

* If the cluster DNS server was slow to start resolving DNS names after a new
  node was started, the session manager could fail on startup and enter crash
  loop back off state. To remedy both session manager and secrets manager now
  ensure DNS is able to resolve cluster control plane DNS name before starting
  up. Startup probes have also been added to these two operators.

* If the cluster DNS didn't return a FQDN for the `kubernetes.default.svc` when
  queried by that name, the value of the `CLUSTER_DOMAIN` variable provided to
  the workshop sessions would be incorrect. This was occuring when Educates was
  installed into some versions of a virtual cluster. When the returned host name
  is not a FQDN, then `cluster.local` will now be used.

* Workshop session dashboard configuration could not in some cases be overridden
  from inside of the workshop session by modifying the injected workshop
  definition. This included not being able to change workshop/terminal layout
  and whether the dashboard tabs for the editor and console were displayed.

* The builtin Google Analytics integration was broken due to the `TrainingPortal`
  Content Security Policy (CSP) directives declaring outdated sources. The CSPs
  now allow for `*.google-analytics.com` and `*.googletagmanager.com` to be
  referenced.

* The `CSRF_ALLOWED_ORIGINS` setting for the `TrainingPortal` Django backend was
  breaking CSRF verification for any `TrainingPortal` with a custom
  `PORTAL_HOSTNAME` configured. We now use the `PORTAL_HOSTNAME` as allowed
  CSRF origin and only fall back to the previous implementation if no custom
  hostname was provided.

* The workshop title in the dropdown TOC of the workshop instructions was not
  being populated with the workshop title from the workshop definition when the
  Hugo renderer was being used.

* If a workshop session had not been registered by the session manager within 30
  seconds of creation and a workshop allocation was pending, the workshop
  allocation would not progress properly to the allocated state and any request
  objects associated with the workshop session would not be created. From the
  perspective of a workshop user the session would still appear to work as the
  workshop dashboard would still be accessible, but request objects would be
  missing. Timeout for workshop session registration has been increased to 90
  seconds.

* If text followed a clickable action and the `cascade` option was used, the
  subsequent clickable action would not be automatically triggered. It would
  work okay if the next clickable action immediately followed the first. This
  was broken when the cascade mechanim was extended to all clickable actions and
  not just examiner clickable actions.
