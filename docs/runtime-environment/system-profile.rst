.. _system-profile-resource:

System Profile
==============

The ``SystemProfile`` custom resource is used to configure the eduk8s operator. The default system profile can be used to set defaults for ingress and image pull secrets, with specific deployments being able to select an alternate profile if required.

The raw custom resource definition for the ``SystemProfile`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/system-profile.yaml

Operator default system profile
-------------------------------

The eduk8s operator will by default use an instance of the ``SystemProfile`` custom resource, if it exists, named ``default-system-profile``. You can override the name of the resource used by the eduk8s operator as the default, by setting the ``SYSTEM_PROFILE`` environment variable on the deployment for the eduk8s operator.

::

    kubectl set env deployment/eduk8s-operator -e SYSTEM_PROFILE=default-system-profile -n eduk8s

Any changes to an instance of the ``SystemProfile`` custom will be automatically detected and used by the eduk8s operator and there is no need to redeploy the operator when changes are made.

Defining configuration for ingress
----------------------------------

The ``SystemProfile`` custom resource replaces the use of environment variables to configure details such as the ingress domain, secret and class.

Instead of setting ``INGRESS_DOMAIN``, ``INGRESS_SECRET`` and ``INGRESS_CLASS`` environment variables, create an instance of the ``SystemProfile`` custom resource named ``default-system-profile``.

.. code-block:: yaml
    :emphasize-lines: 6-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      ingress:
        domain: training.eduk8s.io
        secret: training-eduks8-io-tls
        class: nginx

Defining image registry pull secrets
------------------------------------

If needing to work with custom workshop images stored in a private image registry, the system profile can define a list of image pull secrets that should be added to the service accounts used to deploy and run the workshop images. The ``environment.secrets.pull`` property should be set to the list of secret names.

.. code-block:: yaml
    :emphasize-lines: 6-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      environment:
        secrets:
          pull:
          - private-image-registry-pull

The secrets containing the image registry credentials must exist within the ``eduk8s`` namespace where the eduk8s operator is deployed. The secret resources must be of type ``kubernetes.io/dockerconfigjson``.

Note that this doesn't result in any secrets being added to the namespace created for each workshop session. The secrets are only added to the workshop namespace and are not visible to a user.

For container images used as part of eduk8s itself, such as the container image for the training portal web interface, and the builtin base workshop images, if you have copied these from the public image registries and stored them in a local private registry, instead of the above setting you should use the ``registry`` section as follows.

.. code-block:: yaml
    :emphasize-lines: 6-9

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      registry:
        host: registry.test
        namespace: eduk8s
        secret: eduk8s-image-registry-pull

The ``registry.host`` value should be the hostname of the registry.

The ``registry.namespace`` is a path which can consist of an organization name and/or repository name. If the image registry isn't multi tenant, the ``registry.namespace`` property does not need to be be defined. The ``registry.host``, ``registry.namespace`` if set, and the name of the actual image, including version tag, will be concatenated together separated by '/' to form the full image name.

The ``registry.secret`` is the name of the secret containing the image registry credentials. This must be present in the ``eduk8s`` namespace.

When ``registry.host`` is set, it will override the use in the following eduk8s images of the existing public image registry.

* eduk8s-portal
* base-environment
* jdk8-environment
* jdk11-environment
* conda-environment

Defining storage class for volumes
----------------------------------

Deployments of the training portal web interface and the workshop sessions make use of persistent volumes. By default the persistent volume claims will not specify a storage class for the volume and instead rely on the Kubernetes cluster specifying a default storage class that works. If the Kubernetes cluster doesn't define a suitable default storage class, or you need to override it, you can set the ``storage.class`` property.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      storage:
        class: default

Note that this only applies to persistent volume claims setup by the eduk8s operator. If the steps in a workshop which a user executes include making persistent volume claims, these will not be automatically adjusted.

Defining storage group for volumes
----------------------------------

Where persistent volumes are used by eduk8s for the training portal web interface and workshop environments, the application of the defined pod security policies is relied on to ensure that the security context of pods are updated to give access to volumes. For where the pod security policy admission controller is not enabled, a fallback is instituted to enable access to volumes by enabling group access using the group ID of ``0``.

In situations where the only class of persistent storage available is NFS or similar, it may be necessary to override the group ID applied and set it to an alternate ID dictated by the file system storage provider. If this is required, you can set the ``storage.group`` property.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      storage:
        group: 0

Note that this only applies to the persistent volumes used by eduk8s itself. If a workshop asks users to create persistent volumes, those instructions or the resource definitions used may need to be modified in order to work where the storage class available requires access as a specific group ID.

Overriding network packet size
------------------------------

When support for building container images using ``docker`` is enabled for workshops, because of network layering that occurs when doing ``docker build`` or ``docker run``, it is necessary to adjust the network packet size (mtu) used for containers run from ``dockerd`` hosted inside of the workshop container.

The default mtu size for networks is 1500, but when containers are run in Kubernetes the size available to containers is often reduced. To deal with this possibility, the mtu size used when ``dockerd`` is run for a workshop is set as 1400 instead of 1500.

If you experience problems building or running images with the ``docker`` support, including errors or timeouts in pulling images, or when pulling software packages (PyPi, npm, etc) within a build, you may need to override this value to an even lower value.

If this is required, you can set the ``dockerd.mtu`` property.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      dockerd:
        mtu: 1400

You can determine what the size may need to be by accessing the ``docker`` container run with a workshop and run ``ifconfig eth0``. This will yield something similar to::

    eth0      Link encap:Ethernet  HWaddr 02:42:AC:11:00:07
              inet addr:172.17.0.7  Bcast:172.17.255.255  Mask:255.255.0.0
              UP BROADCAST RUNNING MULTICAST  MTU:1350  Metric:1
              RX packets:270018 errors:0 dropped:0 overruns:0 frame:0
              TX packets:283882 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:0
              RX bytes:86363656 (82.3 MiB)  TX bytes:65183730 (62.1 MiB)

If the ``MTU`` size is less than 1400, then use the value given, or a smaller value, for the ``dockerd.mtu`` setting.

Setting default access credentials
----------------------------------

When deploying a training portal using the ``TrainingPortal`` custom resource, the credentials for accessing the portal will be unique for each instance. The details of the credentials can be found by viewing status information added to the custom resources using ``kubectl describe``.

If you want to override the credentials for the portals so the same set of credentials are used for each, they can be overridden by adding the desired values to the system profile.

To override the username and password for the admin and robot accounts use ``portal.credentials``.

.. code-block:: yaml
    :emphasize-lines: 7-13

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      portal:
        credentials:
          admin:
            username: eduk8s
            password: admin-password
          robot:
            username: robot@eduk8s
            password: robot-password

To override the client ID and secret used for OAuth access by the robot account, use ``portal.clients``.

.. code-block:: yaml
    :emphasize-lines: 7-10

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      portal:
        clients:
          robot:
            id: robot-id
            secret: robot-secret

If the ``TrainingPortal`` has specified credentials or client information, they will still take precedence over the values specified in the system profile.

Overriding the workshop images
------------------------------

When a workshop does not define a workshop image to use, and instead downloads workshop content from GitHub or a web server, the ``base-environment`` workshop image is used. The workshop content is then added to the container, overlaid on this image.

The version of the ``base-environment`` workshop image used is what was the most up to date compatible version of the image available for that version of the eduk8s operator when it was released.

If necessary you can override what version of the ``base-environment`` workshop image is used by defining a mapping under ``workshop.images``. For workshop images supplied as part of the eduk8s project, you can override the short names used to refer to them.

The short versions of the names which are recognised are:

* ``base-environment:*`` - A tagged version of the ``base-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``base-environment:develop`` - The ``develop`` version of the ``base-environment`` workshop image.
* ``base-environment:master`` - The ``master`` version of the ``base-environment`` workshop image.
* ``jdk8-environment:*`` - A tagged version of the ``jdk8-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``jdk8-environment:develop`` - The ``develop`` version of the ``jdk8-environment`` workshop image.
* ``jdk8-environment:master`` - The ``master`` version of the ``jdk8-environment`` workshop image.
* ``jdk11-environment:*`` - A tagged version of the ``jdk11-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``jdk11-environment:develop`` - The ``develop`` version of the ``jdk11-environment`` workshop image.
* ``jdk11-environment:master`` - The ``master`` version of the ``jdk11-environment`` workshop image.
* ``conda-environment:*`` - A tagged version of the ``conda-environment`` workshop image which has been matched with the current version of the eduk8s operator.
* ``conda-environment:develop`` - The ``develop`` version of the ``conda-environment`` workshop image.
* ``conda-environment:master`` - The ``master`` version of the ``conda-environment`` workshop image.

If you wanted to override the version of the ``base-environment`` workshop image mapped to by the ``*`` tag, you would use:

.. code-block:: yaml
    :emphasize-lines: 6-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      workshop:
        images:
          "base-environment:*": "quay.io/eduk8s/base-environment:master"

It is also possible to override where images are pulled from for any arbitrary image. This could be used where you want to cache the images for a workshop in a local image registry and avoid going outside of your network, or the cluster, to get them. This means you wouldn't need to override the workshop definitions for a specific workshop to change it.

.. code-block:: yaml
    :emphasize-lines: 6-8

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      workshop:
        images:
          "quay.io/eduk8s-labs/lab-k8s-fundamentals:master": "registry.test/lab-k8s-fundamentals:master"

Additional custom system profiles
---------------------------------

If the default system profile is specified, it will be used by all deployments managed by the eduk8s operator unless the system profile to use has been overridden for a specific deployment. The name of the system profile can be set for deployments by setting the ``system.profile`` property of ``TrainingPortal``, ``WorkshopEnvironment`` and ``WorkshopSession`` custom resources.

.. code-block:: yaml
    :emphasize-lines: 6-7

    apiVersion: training.eduk8s.io/v1alpha1
    kind: TrainingPortal
    metadata:
      name: lab-markdown-sample
    spec:
      system:
        profile: training-eduk8s-io-profile
      workshops:
      - name: lab-markdown-sample
        capacity: 1
