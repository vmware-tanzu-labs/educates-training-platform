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
    "uid": "91dfa283-fb60-403b-8e50-fb30943ae87d",
    "generation": 2,
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
      "state": "RUNNING",
      "workshop": {
        "name": "lab-markdown-sample",
        "id": "a523b87ab5c9a3c2d1e1265ec141b316",
        "title": "Markdown Sample",
        "description": "A sample workshop using Markdown",
        "vendor": "eduk8s.io",
        "authors": [],
        "difficulty": "beginner",
        "duration": "15m",
        "tags": [],
        "logo": "",
        "url": "https://github.com/vmware-tanzu-labs/lab-markdown-sample"
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

For each workshop listed under ``environments``, where a field listed under ``workshop`` has the same name as it appears in the ``Workshop`` custom resource, it has the same meaning. The ``id`` field is an additional field which tries to uniquely identify a workshop based on the name of the workshop image, the Git repository for the workshop, or the web site hosting the workshop instructions. The value of the ``id`` field doesn't rely on the name of the ``Workshop`` resource and should be the same if same workshop details are used but the name of the ``Workshop`` resource is different.

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

By default, only workshop environments which are currently marked with a ``state`` of ``RUNNING`` are returned. That is, those workshop environments which are taking new workshop session requests. If you also want to see the workshop environments which are currently in the process of being shutdown, you need to provide the ``state`` query string parameter to the REST API call and indicate which states workshop environments should be returned for.

```
curl -v -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/catalog/environments/?state=RUNNING&state=STOPPING
```

The ``state`` query string parameter can be included more than once to be able to see workshop environments in both ``RUNNING`` and ``STOPPING`` states.

Note that if anonymous access to the list of workshop environments is enabled and you are not authenticated when using the REST API endpoint, only workshop environments in a running state will be returned.
