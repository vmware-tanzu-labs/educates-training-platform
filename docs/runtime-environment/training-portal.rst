Training Portal
===============

The ``TrainingPortal`` custom resource triggers the deployment of a set of workshop environments and a set number of workshop instances.

The raw custom resource definition for the ``TrainingPortal`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/training-portal.yaml

Specifying the workshop definitions
-----------------------------------

Running multiple workshop instances to perform training to a group of people can be done by following the step wise process of creating the workshop environment, and then creating each workshop instance. The ``TrainingPortal`` workshop resource bundles that up as one step.

Before creating the training environment you still need to load the workshop definitions as a separate step.

To specify the names of the workshops to be used for the training, list them under the ``workshops`` field of the training portal specification. Each entry needs to define a ``name`` property, matching the name of the ``Workshop`` resource which was created.

.. code-block:: yaml
    :emphasize-lines: 6-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 1

The ``name`` of the training portal specified in the ``metadata`` of the training portal does not need to be the same, and logically would need to be different if creating a training portal for multiple workshops.

When the training portal is created, it will setup the underlying workshop environments, create the required number of workshop instances for each workshop, and deploy a web portal for attendees of the training to access their workshop instances.

Capacity of the training portal
-------------------------------

When setting up the training portal you need to specify a maximum for the number of workshop instances that can be created for each workshop. To do this set the ``capacity`` field under the entry for the workshop. Additional fields can also be set to customize the behaviour further.

.. code-block:: yaml
    :emphasize-lines: 6-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 8
        reserved: 1
        initial: 4

The value of ``capacity`` is a maximum only. How many workshop sessions will be pre-created in advance will depend on how ``reserved`` and ``initial`` is also defined.

If neither ``reserved`` or ``initial`` is defined, then as many workshop sessions as is defined by ``capacity`` will be created up front.

If ``reserved`` is defined but ``initial`` is not defined, then only as many workshop sessions as ``reserved`` specifies will be created up front.

Except where the maximum capacity would be exceeded, each time one of the reserved workshop instances is allocated to a user, a new workshop session will also be created to ensure that the required number of reserved instances are always ready.

If ``initial`` is defined and is larger than ``reserved``, it overrides ``reserved`` for determining the number of workshop sessions created at the start. When workshop instances are allocated, no new instances will be created in reserve to replace them until the number still unallocated drops below ``reserved``.

Irrespective of whether you have multiple workshops listed, if you don't want to provide the settings for each workshop, and instead want them to all use the same values, you can specify these settings against ``portal`` instead.

.. code-block:: yaml
    :emphasize-lines: 6-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        capacity: 8
        reserved: 1
        initial: 4
      workshops:
      - name: lab-markdown-sample

Expiring of workshop sessions
-----------------------------

Once you reach the maximum capacity, no more workshops sessions can be created. Once a workshop session has been allocated to a user, they cannot be re-assigned to another user.

If running a supervised workshop you therefore need to ensure that you set the capacity higher than the expected number in case you have extra users you didn't expect which you need to accomodate. You can use the setting for the reserved number of instances so that although a higher capacity is set, workshop sessions are only created as required, rather than all being created up front.

For supervised workshops when the training is over you would delete the whole training environment and all workshop sessions would then be deleted.

If you need to host a training portal over an extended period and you don't know when users will want to do a workshop, you can setup workshop sessions to expire after a set time. When expired the workshop session will be deleted, and a new workshop session can be created in its place.

The maximum capacity is therefore the maximum at any one point in time, with the number being able to grow and shrink over time. In this way, over an extended time you could handle many more sessions that what the maximum capacity is set to. The maximum capacity is in this case used to ensure you don't try and allocate more workshop sessions than you have resources to handle at any one time.

Setting a maximum time allowed for a workshop session can be done using the ``expires`` setting.

.. code-block:: yaml
    :emphasize-lines: 10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 8
        reserved: 1
        expires: 60m

The value needs to be an integer, followed by a suffix of 's', 'm' or 'h', corresponding to seconds, minutes or hours.

The time period is calculated from when the workshop session is allocated to a user. When the time period is up, the workshop session will be automatically deleted.

When an expiration period is specified, when a user finishes a workshop, or restarts the workshop, it will also be deleted.

To cope with users who grab a workshop session, but then leave and don't actually use it, you can also set a time period for when a workshop session with no activity is deemed as being orphaned and so deleted. This is done using the ``orphaned`` setting.

.. code-block:: yaml
    :emphasize-lines: 11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 8
        reserved: 1
        expires: 60m
        orphaned: 5m

For supervised workshops where the whole event only lasts a certain amount of time, you should avoid this setting so that a users session is not deleted when they take breaks and their computer goes to sleep.

The ``expires`` and ``orphaned`` settings can also be set against ``portal`` instead, if you want to have them apply to all workshops.

Overriding the ingress domain
-----------------------------

In order to be able to access a workshop instance using a public URL, you will need to specify an ingress domain. If an ingress domain isn't specified, the default ingress domain that the eduk8s operator has been configured with will be used.

When setting a custom domain, DNS must have been configured with a wildcard domain to forward all requests for sub domains of the custom domain, to the ingress router of the Kubernetes cluster.

To provide the ingress domain, you can set the ``portal.ingress.domain`` field.

.. code-block:: yaml
    :emphasize-lines: 7-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        ingress:
          domain: training.eduk8s.io
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

If overriding the domain, by default, the workshop session will be exposed using a HTTP connection. If you require a secure HTTPS connection, you will need to have access to a wildcard SSL certificate for the domain. A secret of type ``tls`` should be created for the certificate in the ``eduk8s`` namespace. The name of that secret should then be set in the ``portal.ingress.secret`` field.

.. code-block:: yaml
    :emphasize-lines: 9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        ingress:
          domain: training.eduk8s.io
          secret: training-eduk8s-io-tls
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

If you need to override or set the ingress class, which dictates which ingress router is used when more than one option is available, you can add ``portal.ingress.class``.

.. code-block:: yaml
    :emphasize-lines: 10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        ingress:
          domain: training.eduk8s.io
          secret: training-eduk8s-io-tls
          class: nginx
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

Overriding the portal hostname
------------------------------

The default hostname given to the training portal will be the name of the resource with ``-ui`` suffix, followed by the domain specified by the resource, or the default inherited from the configuration of the eduk8s operator.

If you want to override the generated hostname, you can set ``portal.ingress.hostname``.

.. code-block:: yaml
    :emphasize-lines: 8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        ingress:
          hostname: labs
          domain: training.eduk8s.io
          secret: training-eduk8s-io-tls
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

This will result in the hostname being ``labs.training.eduk8s.io``, rather than the default generated name for this example of ``lab-markdown-sample-ui.training.eduk8s.io``.

Setting extra environment variables
-----------------------------------

If you want to override any environment variables for workshop instances created for a specific work, you can provide the environment variables in the ``env`` field of that workshop.

.. code-block:: yaml
    :emphasize-lines: 10-12

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1
        env:
        - name: REPOSITORY_URL
          value: https://github.com/eduk8s/lab-markdown-sample

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``service_account`` - The name of the service account the workshop instance runs as, and which has access to the namespace created for that workshop instance.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The syntax for referencing one of the parameters is ``$(parameter_name)``.

Overriding portal credentials
-----------------------------

When a training portal is deployed, the username for the admin and robot accounts will use the defaults of ``eduk8s`` and ``robot@eduk8s``. The passwords for each account will be randomly set.

For the robot account, the OAuth application client details used with the REST API will also be randomly generated.

You can see what the credentials and client details are by running ``kubectl describe`` against the training portal resource. This will yield output which includes::

    Status:
      eduk8s:
        Clients:
          Robot:
            Id:      ACZpcaLIT3qr725YWmXu8et9REl4HBg1
            Secret:  t5IfXbGZQThAKR43apoc9usOFVDv2BLE
        Credentials:
          Admin:
            Password:  0kGmMlYw46BZT2vCntyrRuFf1gQq5ohi
            Username:  eduk8s
          Robot:
            Password:  QrnY67ME9yGasNhq2OTbgWA4RzipUvo5
            Username:  robot@eduk8s

If you wish to override any of these values in order to be able to set them to a pre-determined value, you can add ``credentials`` and ``clients`` sections to the training portal specification.

To overload the credentials for the admin and robot accounts use:

.. code-block:: yaml
    :emphasize-lines: 7-13

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        credentials:
          admin:
            username: admin-user
            password: top-secret
          robot:
            username: robot-user
            password: top-secret
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

To override the application client details for OAuth access by the robot account use:

.. code-block:: yaml
    :emphasize-lines: 7-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        clients:
          robot:
            id: application-id
            secret: top-secret
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

Controlling registration type
-----------------------------

By default the training portal web interface will present a registration page for users to create an account, before they can select a workshop to do. If you only want to allow the administrator to login, you can disable the registration page. This would be done if using the REST API to create and allocate workshop sessions from a separate application.

.. code-block:: yaml
    :emphasize-lines: 7-9

    apiVersion: training.eduk8s.io/v1alpha1
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

If rather than requiring users to register, you want to allow anonymous access, you can switch the registration type to anonymous.

.. code-block:: yaml
    :emphasize-lines: 7-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        registration:
          type: anonymous
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

In anonymous mode, when users visit the home page for the training portal an account will be automatically created and they will be logged in.

Specifying an event access code
-------------------------------

Where deploying the training portal with anonymous access, or open registration, anyone would be able to access workshops who knows the URL. If you want to at least prevent access to those who know a common event access code or password, you can set ``portal.password``.

.. code-block:: yaml
    :emphasize-lines: 7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        password: workshops-2020-07-01
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

When the training portal URL is accessed, users will be asked to enter the event access code before they are redirected to the list of workshops (when anonymous access is enabled), or to the login page.

Making list of workshops public
-------------------------------

By default the index page providing the catalog of available workshop images is only available once a user has logged in, be that through a registered account or as an anonymous user.

If you want to make the catalog of available workshops public, so they can be viewed before logging in, you can set the ``portal.catalog.visibility`` property.

.. code-block:: yaml
    :emphasize-lines: 7-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        catalog:
          visibility: public
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

By default the catalog has visibility set to ``private``. Use ``public`` to expose it.

Note that this will also make it possible to access the list of available workshops from the catalog, via the REST API, without authenticating against the REST API.

Using an external list of workshops
-----------------------------------

If you are using the training portal with registration disabled and are using the REST API from a separate web site to control creation of sessions, you can specify an alternate URL for providing the list of workshops.

This helps in the situation where for a session created by the REST API, cookies were deleted, or a session URL was shared with a different user, meaning the value for the ``index_url`` supplied with the REST API request is lost.

The property to set the URL for the external site is ``portal.index``.

.. code-block:: yaml
    :emphasize-lines: 7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        index: https://www.example.com/
        registration:
          type: one-step
          enabled: false
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

If the property is supplied, passing the ``index_url`` when creating a workshop session using the REST API is optional, and the value of this property will be used. You may still want to supply ``index_url`` when using the REST API however if you want a user to be redirected back to a sub category for workshops on the site providing the list of workshops. The URL provided here in the training portal definition would then act only as a fallback when the redirect URL becomes unavailable, and would direct back to the top level page for the external list of workshops.

Note that if a user has logged into the training portal as the admin user, they will not be redirected to the external site and will still see the training portals own list of workshops.

Overriding portal title and logo
--------------------------------

The web interface for the training portal will display a generic eduk8s logo by default, along with a page title of "Workshops". If you want to override these, you can set ``portal.title`` and ``portal.logo``.

.. code-block:: yaml
    :emphasize-lines: 7-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        title: Workshops
        logo: data:image/png;base64,....
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

The ``logo`` field should be a graphical image provided in embedded data URI format which displays the branding you desire. The image is displayed with a fixed height of "40px". The field can also be a URL for an image stored on a remote web server.

Allowing the portal in an iframe
--------------------------------

By default if you try and display the web interface for the training portal in an iframe of another web site, it will be prohibited due to content security policies applying to the training portal web site.

If you want to enable the ability to iframe the full training portal web interface, or even a specific workshop session created using the REST API, you need to provide the hostname of the site which will embed it. This can be done using the ``portal.theme.frame.ancestors`` property.

.. code-block:: yaml
    :emphasize-lines: 7-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      portal:
        theme:
          frame:
            ancestors:
            - https://www.example.com
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

The property is a list of hosts, not a single value. If needing to use a URL for the training portal in an iframe of a page, which is in turn embedded in another iframe of a page on a different site again, the hostnames of all sites need to be listed.

Note that the sites which embed the iframes must be secure and use HTTPS, they cannot use plain HTTP. This is because browser policies prohibit promoting of cookies to an insecure site when embedding using an iframe. If cookies aren't able to be stored, a user would not be able to authenticate against the workshop session.
