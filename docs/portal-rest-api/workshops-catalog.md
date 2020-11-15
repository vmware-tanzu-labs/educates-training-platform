Workshops Catalog
=================

A single training portal can hosted one or more workshops. The REST API endpoints for the workshops catalog provide a means to list the available workshops and get information on them.

Listing available workshops
---------------------------

The URL sub path for accessing the list of available workshop environments is ``/workshops/catalog/environments/``. When making the request, the access token must be supplied in the HTTP ``Authorization`` header with type set as ``Bearer``:

```
curl -v -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/catalog/environments/
```

The JSON response will be of the form:

```
{
  "portal": {
    "name": "lab-markdown-sample",
    "url": "https://lab-markdown-sample-ui.test",
    "sessions": {
      "maximum": 0,
      "registered": 0,
      "anonymous": 0,
      "allocated": 1
    }
  },
  "environments": [
    {
      "name": "lab-markdown-sample-w01",
      "workshop": {
        "name": "lab-markdown-sample",
        "vendor": "eduk8s.io",
        "title": "Markdown Sample",
        "description": "A sample workshop using Markdown",
        "url": "https://github.com/eduk8s/lab-markdown-sample"
      },
      "duration": 3600,
      "capacity": 10,
      "reserved": 2,
      "allocated": 1,
      "available": 2
    }
  ]
}
```

For each workshop listed under ``environments``, where a field has the same name as it appears in the ``Workshop`` custom resource, it has the same meaning.

The ``duration`` field provides the time in seconds after which the workshop environment will be expired. The value can be ``null`` if there is no expiration time for the workshop.

The ``capacity`` field is the maximum number of workshop sessions that can be created for the workshop.

The ``reserved`` field indicates how many instances of the workshop will be reserved as hot spares. These will be used to service requests for a workshop session. If no reserved instances are available and capacity has not been reached, a new workshop session will be created on demand.

The ``allocated`` field indicates how many workshop sessions are active and currently allocated to a user.

The ``available`` field indicates how many workshop sessions are available for immediate allocation. This will never be more than the number of reserved instances.

Under ``portal.sessions``, the ``allocated`` field indicates the total number of allocated sessions across all workshops hosted by the portal.

Where ``maximum``, ``registered`` and ``anonymous`` are non zero, they indicate caps on number of workshops that can be run.

The ``maximum`` indicates a maximum on the total number of workshop sessions that can be run by the portal across all workshops. Even where a specific workshop may not have reached capacity, if ``allocated`` for the whole portal has reached ``maximum``, then no more workshop sessions will be able to be created.

The value of ``registered`` when non zero indicates a cap on the number of workshop sessions a single registered portal user can have running at the one time.

The value of ``anonymous`` when non zero indicates a cap on the number of workshop sessions an anonymous user can have running at the one time. Anonymous users are users created as a result of the REST API being used, or if anonymous access is enabled when accessing the portal via the web interface.
