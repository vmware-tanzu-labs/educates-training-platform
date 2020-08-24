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
    :emphasize-lines: 8-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      sessions:
        maximum: 8
      workshops:
      - name: lab-asciidoc-sample
      - name: lab-markdown-sample

When the training portal is created, it will setup the underlying workshop environments, create any workshop instances required to be created initially for each workshop, and deploy a web portal for attendees of the training to access their workshop instances.

Limiting the number of sessions
-------------------------------

When defining the training portal, you can set a limit on the workshop sessions that can be run concurrently. This is done using the ``sessions.maximum`` property.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      sessions:
        maximum: 8
      workshops:
      - name: lab-asciidoc-sample
      - name: lab-markdown-sample

When this is specified, the maximum capacity of each workshop will be set to the same maximum value for the portal as a whole. This means that any one workshop can have as many sessions as specified by the maximum, but to achieve that only instances of that workshops could have been created. In other words the maximum applies to the total number of workshop instances created across all workshops.

Note that if you do not set ``sessions.maximum``, you must set the capacity for each individual workshop as detailed below. In only setting the capacities of each workshop and not an overall maximum for sessions, you can't share the overall capacity of the training portal across multiple workshops.

Capacity of individual workshops
--------------------------------

When you have more than one workshop, you may want to limit how many instances of each workshop you can have so that they cannot grow to the maximum number of sessions for the whole training portal, but a lessor maximum. This means you can stop one specific workshop taking over all the capacity of the whole training portal. To do this set the ``capacity`` field under the entry for the workshop.

.. code-block:: yaml
    :emphasize-lines: 10,12

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      sessions:
        maximum: 8
      workshops:
      - name: lab-asciidoc-sample
        capacity: 4
      - name: lab-markdown-sample
        capacity: 6

The value of ``capacity`` caps the number of workshop sessions for the specific workshop at that value. It should always be less than or equal to the maximum number of workshops sessions as the latter always sets the absolute cap.

Set reserved workshop instances
-------------------------------

By default, one instance of each of the listed workshops will be created up front so that when the initial user requests that workshop, it is available for use immediately.

When such a reserved instance is allocated to a user, provided that the workshop capacity hasn't been reached a new instance of the workshop will be created as a reserve ready for the next user. When a user ends a workshop, if the workshop had been at capacity, when the instance is deleted, then a new reserve will be created. The total of allocated and reserved sessions for a workshop cannot therefore exceed the capacity for that workshop.

If you want to override for a specific workshop how many reserve instances are kept in standby ready for users, you can set the ``reserved`` setting against the workshop.

.. code-block:: yaml
    :emphasize-lines: 11,14

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      sessions:
        maximum: 8
      workshops:
      - name: lab-asciidoc-sample
        capacity: 4
        reserved: 2
      - name: lab-markdown-sample
        capacity: 6
        reserved: 4

The value of ``reserved`` can be set to 0 if you do not ever want any reserved instances for a workshop and you instead only want instances of that workshop created on demand when required for a user. Only creating instances of a workshop on demand can result in a user needing to wait longer to access their workshop session.

Note that in this instance where workshop instances are always created on demand, but also in other cases where reserved instances are tying up capacity which could be used for a new session of another workshop, the oldest reserved instance will be terminated to allow a new session of the other workshop to be created. This will occur so long as any caps for specific workshops are being satisfied.

Override initial number of sessions
-----------------------------------

The initial number of workshop instances created for each workshop will be what is specified by ``reserved``, or 1 if the setting wasn't provided.

In the case where ``reserved`` is set in order to keep workshop instances on standby, you can indicate that initially you want more than the reserved number of instances created. This is useful where you are running a workshop for a set period of time. You might create up front instances of the workshop corresponding to 50% of the expected number of attendees, but with a smaller reserve number. With this configuration, new reserve instances would only start to be created when getting close to the 50% and all of the extra instances created up front have been allocated to users. This way you aren't creating more workshop instances than necessary if not as many people turn up to the workshop as you expect.

.. code-block:: yaml
    :emphasize-lines: 10-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: kubernetes-fundamentals
    spec:
      sessions:
        maximum: 100
      workshops:
      - name: lab-kubernetes-fundamentals
        initial: 50
        reserved: 10

Setting defaults for all workshops
----------------------------------

If you have a list of workshops and they all need to be set with the same values for ``capacity``, ``reserved`` and ``initial``, rather than add the settings to each, you can set defaults to apply to each under the ``portal`` section instead.

.. code-block:: yaml
    :emphasize-lines: 9-11

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      portal:
        sessions:
          maximum: 10
        capacity: 6
        reserved: 2
        initial: 4
      workshops:
      - name: lab-asciidoc-sample
      - name: lab-markdown-sample

Note that the location of these defaults in the training portal configuration will most likely change in a future version.

Setting caps on individual users
--------------------------------

By default a single user can run more than one workshop at a time. You can though cap this if you want to ensure that they can only run one at a time. This avoids the problem of a user wasting resources by starting more than one at the same time, but only proceeding with one, without shutting down the other first.

The setting to apply a limit on how many concurrent workshop sessions a user can start is ``sessions.registered``.

.. code-block:: yaml
    :emphasize-lines: 8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      sessions:
        maximum: 8
        registered: 1
      workshops:
      - name: lab-asciidoc-sample
        capacity: 4
        reserved: 2
      - name: lab-markdown-sample
        capacity: 6
        reserved: 4

This limit will also apply to anonymous users when anonymous access is enabled through the training portal web interface, or if sessions are being created via the REST API. If you want to set a distinct limit on anonymous users, you can set ``sessions.anonymous`` instead.

.. code-block:: yaml
    :emphasize-lines: 8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: sample-workshops
    spec:
      sessions:
        maximum: 8
        anonymous: 1
      workshops:
      - name: lab-asciidoc-sample
        capacity: 4
        reserved: 2
      - name: lab-markdown-sample
        capacity: 6
        reserved: 4

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

Tracking using Google Analytics
-------------------------------

If you want to record analytics data on usage of workshops, you can enable tracking for a training portal using Google Analytics.

.. code-block:: yaml
    :emphasize-lines: 6-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      analytics:
        google:
          trackingId: UA-XXXXXXX-1
      workshops:
      - name: lab-markdown-sample
        capacity: 3
        reserved: 1

Custom dimensions are used in Google Analytics to record details about the workshop a user is doing, and through which training portal and cluster it was accessed. You can therefore use the same Google Analytics tracking ID for multiple training portal instances running on different Kubernetes clusters if desired.

To support use of custom dimensions in Google Analytics you must configure the Google Analytics property with the following custom dimensions. They must be added in the order shown as Google Analytics doesn't allow you to specify the index position for a custom dimension and will allocate them for you. You can't already have custom dimensions defined for the property, as the new custom dimensions must start at index of 1.

+-----------------------+-------+
| Custom Dimension Name | Index |
+=======================+=======+
| workshop_name         | 1     |
+-----------------------+-------+
| session_namespace     | 2     |
+-----------------------+-------+
| workshop_namespace    | 3     |
+-----------------------+-------+
| training_portal       | 4     |
+-----------------------+-------+
| ingress_domain        | 5     |
+-----------------------+-------+
| ingress_protocol      | 6     |
+-----------------------+-------+

In addition to custom dimensions against page accesses, events are also generated. These include:

* Workshop/Start
* Workshop/Finish
* Workshop/Expired

If a Google Analytics tracking ID is provided with the ``TrainingPortal`` resource definition, it will take precedence over one set by the ``SystemProfile`` resource definition.
