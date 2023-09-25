Session Management
==================

The REST API endpoints for session management allow you to request that a workshop session be allocated.

Disabling portal user registration
----------------------------------

When using the REST API to trigger creation of workshop sessions, it is recommended that user registration through the training portal web interface be disabled. This will mean that only the admin user will be able to access the web interface for the training portal directly.

```
apiVersion: training.educates.dev/v1beta1
kind: TrainingPortal
metadata:
  name: lab-markdown-sample
spec:
  portal:
    registration:
      type: one-step
      enabled: false
  workshops:
  - name: lab-markdown-sample
    capacity: 3
    reserved: 1
```

(requesting-a-workshop-session)=
Requesting a workshop session
-----------------------------

The form of the URL sub path for requesting the allocation of a workshop environment via the REST API is ``/workshops/environment/<name>/request/``. The name segment needs to be replaced with the name of the workshop environment. When making the request, the access token must be supplied in the HTTP ``Authorization`` header with type set as ``Bearer``:

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/environment/<name>/request/?index_url=https://hub.test/
```

A query string parameter ``index_url`` can be supplied. When the workshop session is restarted from the workshop environment web interface, the session will be deleted, and the user will then be redirected to the supplied URL. This URL would be that for your front end web application which has requested the workshop session, allowing them to select a different workshop.

Note that the value of the ``index_url`` will not be available if session cookies are cleared, or a session URL is shared with another user. In this case a user would be redirected back to the training portal URL instead. You can override the global default for this case by specifying the index URL as part of the ``TrainingPortal`` configuration.

When successful, the JSON response from the request will be of the form:

```
{
    "name": "lab-markdown-sample-w01-s001",
    "user": "8d2d0c8b-6ff5-4244-b136-110fd8d8431a",
    "url": "/workshops/session/lab-markdown-sample-w01-s001/activate/?token=6UIW4D8Bhf0egVmsEKYlaOcTywrpQJGi&index_url=https%3A%2F%2Fhub.test%2F",
    "workshop": "lab-markdown-sample",
    "environment": "lab-markdown-sample-w01",
    "namespace": "lab-markdown-sample-w01-s001"
}
```

This will include the name of the workshop session, an ID for identifying the user, and a URL path with an activation token and index URL included as query string parameters.

The users browser should be redirected to this URL path on the training portal host. Accessing the URL will activate the workshop session and then redirect the user to the workshop dashboard.

If the workshop session is not activated, which confirms allocation of the session, the session will by default deleted after 60 seconds. The length of this activation timeout can be overridden by specifying a query string parameter called ``timeout`` with the desired value in seconds.

When a user is redirected back to the URL for the index page, a query string parameter will be supplied to notify of the reason the user is being returned. This can be used to display a banner or other indication as to why they were returned.

The name of the query string parameter is ``notification`` and the possible values are:

* ``session-deleted`` - Used when the workshop session was completed or restarted.
* ``workshop-invalid`` - Used when the name of the workshop environment supplied when attempting to create the workshop was invalid.
* ``session-unavailable`` - Used when capacity has been reached and a workshop session cannot be created.
* ``session-invalid`` - Used when an attempt is made to access a session which doesn't exist. This can occur when the workshop dashboard is refreshed sometime after the workshop session had expired and been deleted.
* ``startup-timeout`` - Used when a startup timeout was specified for a workshop and it didn't start within the required time.

Note that in prior versions the name of the session was returned via the "session" property, where as the "name" property is now used. To support older code using the REST API, the "session" property is still returned, but it is deprecated and will be removed in a future version.

Associating sessions with a user
--------------------------------

When the workshop session is requested, a unique user account will be created in the training portal each time. This can if necessary be identified through the use of the ``user`` identifier returned in the response.

If the front end using the REST API to create workshop sessions is tracking user activity, to have the training portal associate all workshops sessions created by the same user, supply the ``user`` identifier with subsequent requests by the same user in the request parameter:

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/environment/<name>/request/?index_url=https://hub.test/&user=<user>
```

If the supplied ID matches a user in the training portal, it will be used internally by the training portal, and the same value will be returned for ``user`` in the response.

When the user does match, if there is already a workshop session allocated to the user for the workshop environment the request is made against, a link to the existing workshop session will be returned rather than creating a new workshop session.

Where the front end using the REST API has it's own globally unique concept of a user ID, it can supply it using the ``user`` param in all requests. When this is done, rather than the training portal generating a user identifier the supplied identifier will be used instead. In this case the ``user`` parameter returned with the response will always match that supplied with the request.

In a situation where the training portal had been deleted and redeployed since the last time it was accessed, in cases where the ``user`` identifier had originally been created by a prior instance of the training portal, that user identifier will end up carrying over to the new training portal instance. 

When making a request to create a workshop session you can optionally supply request parameters for the following to have these set as the user details in the training portal.

* ``email`` - The email address of the user.
* ``first_name`` - The first name of the user.
* ``last_name`` - The last name of the user.

As you wouldn't know whether this is the first time the user had been seen for a specific instance of the training portal, they will need to be supplied with all requests.

The details of the user will be accessible through the admin pages of the training portal for debugging issues, but aren't otherwise used for anything.

When sessions are being associated with a user, it is possible to query all active sessions for that user across the different workshops hosted by the instance of the training portal:

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/user/<user>/sessions/
```

The response will be of the form:

```
{
  "user": "8d2d0c8b-6ff5-4244-b136-110fd8d8431a",
  "sessions": [
    {
      "name": "lab-markdown-sample-w01-s001",
      "workshop": "lab-markdown-sample",
      "environment": "lab-markdown-sample-w01",
      "namespace": "lab-markdown-sample-w01-s001",
      "started": "2020-07-31T03:57:33.942Z",
      "expires": "2020-07-31T04:57:33.942Z",
      "countdown": 3353,
      "extendable": false
    }
  ]
}
```

Once a workshop has expired, or has otherwise been shutdown, an entry for the workshop will no longer be returned.

Note that since workshop environments can be periodically recycled and thus the name of a workshop environment for a workshop will change, if wanting to be able to attach to an existing workshop session, it would be necessary to check the active sessions for the user to see if one exists for the workshop. If one does exist, first make a request against the workshop environment pertaining to the existing workshop session. If that fails, only then would you go through the list of workshop environments to determine which is that for the workshop and make a request against it.

Supplying request parameters
----------------------------

The REST API call for requesting a workshop session can be a HTTP ``GET`` or ``POST`` request.

When using a ``POST`` request it is possible to supply a request body with ``Content-type`` of ``application/json`` in which can be supplied parameters for the workshop session.

```yaml
{
  "parameters": [
    {
      "name": "WORKSHOP_USERNAME",
      "value": "grumpy"
    }
  ]
}
```

The workshop definition must declare in ``request.parameters`` what parameters are expected, along with any default values for the case where they are not supplied when requesting a workshop session.

For more details on configuring a workshop for request parameters and how to use them, see [Passing parameters to a session](passing-parameters-to-a-session)
  and [Resource creation on allocation](resource-creation-on-allocation).

(retrieving-session-configuration)=
Retrieving session configuration
--------------------------------

Each workshop session will be configured specific to that session. A range of variables are available within the workshop container as environment variables and when interpolating workshop instructions, as well as other configuration files.

When necessary a custom frontend portal can query this set of variables directly from a workshop session. In order to do this a special access token is required for that workshop session. Using the REST API of the training portal it is possible to query what this access token is for a specific workshop session and what the URL for the workshop session is.

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/session/<name>/config/
```

The response will be of the form:

```
{
  "url": "https://lab-markdown-sample-w01-s001.test/",
  "password": "secret-token"
}
```

Separate HTTP requests can then be made against the workshop session for different configuration types in the form:

```
curl "<url>/workshop/config/<type>?token=<password>"
```

The type of configuration items that can be requested are:

* ``environment`` - Shell environment variables.
* ``variables`` - Workshop instruction variables.
* ``kubeconfig`` - Kubernetes configuration.
* ``id_rsa`` - Private SSH key.
* ``id_rsa.pub`` - Public SSH key.

Depending on the configuration type these will either be a JSON/YAML response or the raw file.

If the special access token for accessing the workshop configuration is required inside of the workshop container, it is available in the ``config_password`` variable in workshop instructions and as the environment variable ``CONFIG_PASSWORD``.

Listing all workshop sessions
-----------------------------

To get a list of all running workshops sessions allocated to users, you can provide the ``sessions=true`` flag to the query string parameters of the REST API call for listing the workshop environments available through the training portal.

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/catalog/environments/?sessions=true
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
      },
      "duration": 3600,
      "capacity": 10,
      "reserved": 2,
      "allocated": 1,
      "available": 2,
      "sessions": [
        {
          "name": "lab-markdown-sample-w01-s001",
          "namespace": "lab-markdown-sample-w01-s001",
          "user": "8d2d0c8b-6ff5-4244-b136-110fd8d8431a",
          "started": "2020-07-31T03:57:33.942Z",
          "expires": "2020-07-31T04:57:33.942Z",
          "countdown": 3353,
          "extendable": false
        }
      ]
    }
  ]
}
```

No workshop sessions will be returned if anonymous access to this REST API endpoint is enabled and you are not authenticated against the training portal.

Only workshop environments with a ``state`` of ``RUNNING`` will be returned by default. If you want to see workshop environments which are being shutdown, and any workshop sessions against those which still haven't been completed, supply the ``state`` query string parameter with value ``STOPPING``.

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/workshops/catalog/environments/?sessions=true&state=RUNNING&state=STOPPING
```

The ``state`` query string parameter can be included more than once to be able to see workshop environments in both ``RUNNING`` and ``STOPPING`` states.

Extending a workshop session
----------------------------

When a workshop user is interacting with a workshop they will get a visual warning in the workshop dashboard that the workshop expiration time is approaching. If the workshop definition is configured to allow it, clicking on the workshop dashboard countdown clock when it turns orange will extend the time duration for the workshop session.

Subject to the same restriction that the workshop definition must be configured to allow extensions and that it is close to expiring, a REST API call can also be used to extend the workshop session.

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/session/<name>/extend/
```

The response will be similar to:

```
{
  "name": "lab-markdown-sample-w01-s001",
  "namespace": "lab-markdown-sample-w01-s001",
  "user": "8d2d0c8b-6ff5-4244-b136-110fd8d8431a",
  "started": "2020-07-31T03:57:33.942Z",
  "expires": "2020-07-31T04:57:33.942Z",
  "countdown": 3353,
  "extendable": false
}
```

To determine in advance if a workshop session is extendable, one can use:

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/session/<name>/schedule/
```

The response will be similar to that above. If the ``extendable`` property in the response is ``true`` then the workshop session is extendable.

Terminating a workshop session
------------------------------

A workshop session will expire automatically when its expiration time is reached. A workshop user can also end a workshop session early by completing it, or terminating it through the workshop session dashboard.

If you want to terminate a workshop session through the REST API, you can use:

```
curl -H "Authorization: Bearer <access-token>" https://lab-markdown-sample-ui.test/session/<name>/terminate/
```
