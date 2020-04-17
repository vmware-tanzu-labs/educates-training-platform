Session Management
==================

The REST API endpoints for session management allow you to request that a workshop session be allocated.

Requesting a workshop session
-----------------------------

The form of the URL sub path for requesting the allocation of a workshop environment is ``/workshops/environment/<name>/request/``. The name segment needs to be replaced with the name of the workshop environment. When making the request, the access token must be supplied in the HTTP ``Authorization`` header with type set as ``Bearer``::

    curl -v -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/environment/<name>/request/?redirect_url=https://hub.test/

A query string parameter ``redirect_url`` must be supplied. When the workshop session is restarted from the workshop environment web interface, the session will be deleted, and the user will then be redirected to the supplied URL. This URL would be that for your front end web application which has requested the workshop session, allowing them to select a different workshop.

When successful, the JSON response from the request will be of the form::

    {
        "session": "lab-markdown-sample-w01-s001",
        "url": "/workshops/session/lab-markdown-sample-w01-s001/activate/?token=6UIW4D8Bhf0egVmsEKYlaOcTywrpQJGi"
    }

This will return the name of the workshop session, and a URL path, with activation token included as a query string parameter.

The users browser should be redirected to this URL path on the training portal host. Accessing the URL will activate the workshop session and then redirect the user to the workshop dashboard.

If the workshop session is not activated, which confirms allocation of the session, the session will be deleted after 60 seconds.
