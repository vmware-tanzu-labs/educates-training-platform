Version 3.0.1
=============

Upcoming Changes
----------------

For details on significant changes in future versions, including feature
deprecations and removals which may necessitate updates to existing workshops,
see [Upcoming changes](upcoming-changes).

Bugs Fixed
----------

* When the `kind` infastructure provider was selected for the opinionated
  installer, if a CA certificate was provided and installation of `educates`
  training platform component was being disabled, the latter was still being
  installed even though disabled.
