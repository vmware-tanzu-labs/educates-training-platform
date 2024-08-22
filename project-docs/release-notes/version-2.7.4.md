Version 2.7.4
=============

Upcoming Changes
----------------

For details on significant changes in future versions, including feature
deprecations and removals which may necessitate updates to existing workshops,
see [Upcoming changes](upcoming-changes).

Backported Changes
------------------

* When an index URL was supplied to the training portal in the `TrainingPortal`
  resource, or via the REST API, if the URL had query string parameters, the
  query string param added by the training platform with the notification
  message, was not being merged with the existing set of query string parameters
  and was instead being added to the value of the last query string parameter in
  the URL.
