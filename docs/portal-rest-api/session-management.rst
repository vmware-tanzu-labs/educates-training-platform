Session Management
==================

The REST API endpoints for session management allow you to request that a workshop session be allocated.

Disabling portal user registration
----------------------------------

When using the REST API to trigger creation of workshop sessions, it is recommended that user registration through the training portal web interface be disabled. This will mean that only the admin user will be able to access the web interface for the training portal directly.

.. code-block:: yaml
    :emphasize-lines: 9-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 3
        reserved: 1
        registration:
          type: one-step
          enabled: false
      workshops:
      - name: lab-markdown-sample

Requesting a workshop session
-----------------------------

The form of the URL sub path for requesting the allocation of a workshop environment via the REST API is ``/workshops/environment/<name>/request/``. The name segment needs to be replaced with the name of the workshop environment. When making the request, the access token must be supplied in the HTTP ``Authorization`` header with type set as ``Bearer``::

    curl -v -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/environment/<name>/request/?index_url=https://hub.test/

A query string parameter ``index_url`` must be supplied. When the workshop session is restarted from the workshop environment web interface, the session will be deleted, and the user will then be redirected to the supplied URL. This URL would be that for your front end web application which has requested the workshop session, allowing them to select a different workshop.

When successful, the JSON response from the request will be of the form::

    {
        "session": "lab-markdown-sample-w01-s001",
        "user": "8d2d0c8b-6ff5-4244-b136-110fd8d8431a",
        "url": "/workshops/session/lab-markdown-sample-w01-s001/activate/?token=6UIW4D8Bhf0egVmsEKYlaOcTywrpQJGi&index_url=https%3A%2F%2Fhub.test%2F"
    }

This will return the name of the workshop session, an ID for identifying the user, and a URL path with an activation token and index URL included as query string parameters.

The users browser should be redirected to this URL path on the training portal host. Accessing the URL will activate the workshop session and then redirect the user to the workshop dashboard.

If the workshop session is not activated, which confirms allocation of the session, the session will be deleted after 60 seconds.

When a user is redirected back to the URL for the index page, a query string parameter will be supplied to notify of the reason the user is being returned. This can be used to display a banner or other indication as to why they were returned.

The name of the query string parameter is ``notification`` and the possible values are:

* ``session-deleted`` - Used when the workshop session was completed or restarted.
* ``workshop-invalid`` - Used when the name of the workshop environment supplied when attempting to create the workshop was invalid.
* ``session-unavailable`` - Used when capacity has been reached and a workshop session cannot be created.
* ``session-invalid`` - Used when an attempt is made to access a session which doesn't exist. This can occur when the workshop dashboard is refreshed sometime after the workshop session had expired and been deleted.

Associating sessions with a user
--------------------------------

When the workshop session is requested, a unique user account will be created in the training portal each time. This can if necessary be identified through the use of the ``user`` identifier returned in the response.

If the front end using the REST API to create workshop sessions is tracking user activity, to have the training portal associate all workshops sessions created by the same user, supply the ``user`` identifier with subsequent requests by the same user in the request parameter::

    curl -v -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/environment/<name>/request/?index_url=https://hub.test/&user=<user>

If the supplied ID matches a user in the training portal, it will be used internally by the training portal, and the same value will be returned for ``user`` in the response.

If there is no matching user, possibly because the training portal had been completely redeployed since the last time it was accessed, a new user identifier will be returned.

The first time that a request is made to create a workshop session for a user, where ``user`` is not supplied, you can optionally supply request parameters  for the following to have these set as the user details in the training portal.

* ``email`` - The email address of the user.
* ``first_name`` - The first name of the user.
* ``last_name`` - The last name of the user.

These details will be accessible through the admin pages of the training portal.
