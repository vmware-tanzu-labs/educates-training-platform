Workshops Catalog
=================

A single training portal can hosted one or more workshops. The REST API endpoints for the workshops catalog provide a means to list the available workshops and get information on them.

Listing available workshops
---------------------------

The URL sub path for accessing the list of available workshop environments is ``/workshops/catalog/environments/``. When making the request, the access token must be supplied in the HTTP ``Authorization`` header with type set as ``Bearer``::

    curl -v -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/catalog/environments/

The JSON response will be of the form::

    {
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

Where a field has the same name as it appears in the ``Workshop`` custom resource, it has the same meaning.

The ``duration`` field provides the time in seconds after which the workshop environment will be expired. The value can be ``null`` if there is no expiration time for the workshop.

The ``capacity`` field is the maximum number of workshop sessions that can be created for the workshop.

The ``reserved`` field indicates how many instances of the workshop will be reserved as hot spares. These will be used to service requests for a workshop session. If no reserved instances are available and capacity has not been reached, a new workshop session will be created on demand.

The ``allocated`` field indicates how many workshop sessions are active and currently allocated to a user.

The ``available`` field indicates how many workshop sessions are available for immediate allocation. This will never be more than the number of reserved instances.
