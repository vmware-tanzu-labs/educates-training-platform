System Profile
==============

The ``SystemProfile`` custom resource is used to configure the eduk8s operator. The default system profile can be used to set defaults for ingress and image pull secrets, with specific deployments being able to select an alternate profile if required.

The raw custom resource definition for the ``SystemProfile`` custom resource can be viewed at:

* [https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/system-profile.yaml](https://github.com/eduk8s/eduk8s/blob/develop/resources/crds-v1/system-profile.yaml)

Operator default system profile
-------------------------------

The eduk8s operator will by default use an instance of the ``SystemProfile`` custom resource, if it exists, named ``default-system-profile``. You can override the name of the resource used by the eduk8s operator as the default, by setting the ``SYSTEM_PROFILE`` environment variable on the deployment for the eduk8s operator.

```text
kubectl set env deployment/eduk8s-operator -e SYSTEM_PROFILE=default-system-profile -n eduk8s
```

Any changes to an instance of the ``SystemProfile`` custom will be automatically detected and used by the eduk8s operator and there is no need to redeploy the operator when changes are made.

Defining configuration for ingress
----------------------------------

The ``SystemProfile`` custom resource replaces the use of environment variables to configure details such as the ingress domain, secret and class.

Instead of setting ``INGRESS_DOMAIN``, ``INGRESS_SECRET`` and ``INGRESS_CLASS`` environment variables, create an instance of the ``SystemProfile`` custom resource named ``default-system-profile``.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  ingress:
    domain: training.eduk8s.io
    secret: training.eduks8.io-tls
    class: nginx
```

If HTTPS connections are being terminated using an external load balancer and not by specificying a secret for ingresses managed by the Kubernetes ingress controller, with traffic then routed into the Kubernetes cluster as HTTP connections, you can override the ingress protocol without specifying an ingress secret.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  ingress:
    domain: training.eduk8s.io
    protocol: https
    class: nginx
```

Defining image registry pull secrets
------------------------------------

If needing to work with custom workshop images stored in a private image registry, the system profile can define a list of image pull secrets that should be added to the service accounts used to deploy and run the workshop images. The ``environment.secrets.pull`` property should be set to the list of secret names.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  environment:
    secrets:
      pull:
      - private-image-registry-pull
```

The secrets containing the image registry credentials must exist within the ``eduk8s`` namespace where the eduk8s operator is deployed. The secret resources must be of type ``kubernetes.io/dockerconfigjson``.

Note that this doesn't result in any secrets being added to the namespace created for each workshop session. The secrets are only added to the workshop namespace and are not visible to a user.

For container images used as part of eduk8s itself, such as the container image for the training portal web interface, and the builtin base workshop images, if you have copied these from the public image registries and stored them in a local private registry, instead of the above setting you should use the ``registry`` section as follows.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  registry:
    host: registry.test
    namespace: eduk8s
    secret: eduk8s-image-registry-pull
```

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

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  storage:
    class: default
```

Note that this only applies to persistent volume claims setup by the eduk8s operator. If the steps in a workshop which a user executes include making persistent volume claims, these will not be automatically adjusted.

Defining storage group for volumes
----------------------------------

Where persistent volumes are used by eduk8s for the training portal web interface and workshop environments, the application of pod security policies by the cluster is relied on to ensure that the permissions of persistent volumes are set correctly such that they can be accessed by containers mounting the persistent volume. For where the pod security policy admission controller is not enabled, a fallback is instituted to enable access to volumes by enabling group access using the group ID of ``0``.

In situations where the only class of persistent storage available is NFS or similar, it may be necessary to override the group ID applied and set it to an alternate ID dictated by the file system storage provider. If this is required, you can set the ``storage.group`` property.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  storage:
    group: 1
```

Overriding the group ID to match the persistent storage relies on the group having write permission to the volume. If only the owner of the volume has permission this will not work.

In this case it is necessary to change the owner/group and permissions of the persistent volume such that the owner matches the user ID a container runs as, or the group is set to a known ID which is added as a supplemental group for the container, and the persistent volume updated to be writable to this group. This needs to be done by an init container running in the pod mounting the persistent volume.

To trigger this fixup of ownership and permissions, you can set the ``storage.user`` property.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  storage:
    user: 1
    group: 1
```

This will result in the init container being run as the root user, with the owner of the mount directory of the persistent volume being set to ``storage.user``, the group being set to ``storage.group``, and the directory being made group writable. The group will then be added as supplemental group to containers using the persistent volume so they can write to it, regardless of what user ID the container runs as. To that end, the value of ``storage.user`` doesn't matter, as long as it is set, but it may need to be set to a specific user ID based on requirements of the storage provider.

Note that both these variations on the settings only apply to the persistent volumes used by eduk8s itself. If a workshop asks users to create persistent volumes, those instructions or the resource definitions used may need to be modified in order to work where the storage class available requires access as a specific user or group ID. Further, the second method using the init container to fixup permissions will not work if pod security policies are enforced, as the ability to run a container as the root user would be blocked in that case due to the restricted PSP which is applied to workshop instances.

Running docker daemon rootless
------------------------------

If ``docker`` is enabled for workshops, docker in docker is run using a side car container. Because of the current state of running docker in docker, and portability across Kubernetes environments, the ``docker`` daemon by default runs as ``root``. Because a privileged container is also being used, this represents a security risk and workshops requiring ``docker`` should only be run in disposable Kubernetes clusters, or for users who you trust.

The risks of running ``docker`` in the Kubernetes cluster can be partly mediated by running the ``docker`` daemon in rootless mode, however not all Kubernetes clusters may support this due to the Linux kernel configuration or other incompatibilities.

To enable rootless mode, you can set the ``dockerd.rootless`` property to ``true``.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  dockerd:
    rootless: true
```

Use of ``docker`` can be made even more secure by avoiding the use of a privileged container for the ``docker`` daemon. This requires specific configuration to be setup for nodes in the Kubernetes cluster. If such configuration has been done, you can disable the use of a privileged container by setting ``dockerd.privileged`` to ``false``.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  dockerd:
    rootless: true
    privileged: false
```

For further details on the requirements for running rootless docker in docker, and using an non privileged container see:

* [https://docs.docker.com/engine/security/rootless/](https://docs.docker.com/engine/security/rootless/)

Overriding network packet size
------------------------------

When support for building container images using ``docker`` is enabled for workshops, because of network layering that occurs when doing ``docker build`` or ``docker run``, it is necessary to adjust the network packet size (mtu) used for containers run from ``dockerd`` hosted inside of the workshop container.

The default mtu size for networks is 1500, but when containers are run in Kubernetes the size available to containers is often reduced. To deal with this possibility, the mtu size used when ``dockerd`` is run for a workshop is set as 1400 instead of 1500.

If you experience problems building or running images with the ``docker`` support, including errors or timeouts in pulling images, or when pulling software packages (PyPi, npm, etc) within a build, you may need to override this value to an even lower value.

If this is required, you can set the ``dockerd.mtu`` property.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  dockerd:
    mtu: 1400
```

You can determine what the size may need to be by accessing the ``docker`` container run with a workshop and run ``ifconfig eth0``. This will yield something similar to:

```text
eth0      Link encap:Ethernet  HWaddr 02:42:AC:11:00:07
          inet addr:172.17.0.7  Bcast:172.17.255.255  Mask:255.255.0.0
          UP BROADCAST RUNNING MULTICAST  MTU:1350  Metric:1
          RX packets:270018 errors:0 dropped:0 overruns:0 frame:0
          TX packets:283882 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:86363656 (82.3 MiB)  TX bytes:65183730 (62.1 MiB)
```

If the ``MTU`` size is less than 1400, then use the value given, or a smaller value, for the ``dockerd.mtu`` setting.

Image registry pull through cache
---------------------------------

When running or building container images with ``docker``, if the container image is hosted on Docker Hub it will be pulled down direct from Docker Hub for each separate workshop session of that workshop.

Because the image is pulled from Docker Hub this will be slow for all users, especially for large images. With Docker Hub introducing limits on how many images can be pulled anonymously from an IP address within a set period, this also could result in the cap on image pulls being reached, preventing the workshop from being used until the period expires.

Docker Hub has a higher limit when pulling images as an authenticated user, but with the limit being applied to the user rather than by IP address. For authenticated users with a paid plan on Docker Hub, there is no limit.

To try and avoid the impact of the limit, the first thing you can do is enable an image registry mirror with image pull through. This is enabled globally and results in an instance of an image registry mirror being created in the workshop environment of workshops which enable ``docker`` support. This mirror will be used for all workshops sessions created against that workshop environment. When the first user attempts to pull an image, it will be pulled down from Docker Hub and cached in the mirror. Subsequent users will be served up from the image registry mirror, avoiding the need to pull the image from Docker Hub again. The subsequent users will also see a speed up in pulling the image because the mirror is deployed to the same cluster.

For enabling the use of an image registry mirror against Docker Hub, use:

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  dockerd:
    mirror:
      remote: https://registry-1.docker.io
```

For authenticated access to Docker Hub, create an access token under your Docker Hub account. Then set the ``username`` and ``password``, using the access token as the ``password``. Do not use the password for the account itself. Using an access token makes it easier to revoke the token if necessary.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  dockerd:
    mirror:
      remote: https://registry-1.docker.io
      username: username
      password: access-token
```

Note that an access token provides write access to Docker Hub. It is thus also recommended you use a separate robot account in Docker Hub which isn't going to be used to host images, and also doesn't have write access to any other organizations. In other words, use it purely for reading images from Docker Hub.

If this is a free account, the higher limit on image pulls will then apply. If the account is paid, then there may be higher limits, or no limit all all.

Also note that the image registry mirror is only used when running or building images using the support for running ``docker``. The mirror does not come into play when creating deployments in Kubernetes which make use of images hosted on Docker Hub. Usage of images from Docker Hub in deployments will still be subject to the limit for anonymous access, unless you were to supply image registry credentials for the deployment so an authenticated user were used.

Setting default access credentials
----------------------------------

When deploying a training portal using the ``TrainingPortal`` custom resource, the credentials for accessing the portal will be unique for each instance. The details of the credentials can be found by viewing status information added to the custom resources using ``kubectl describe``.

If you want to override the credentials for the portals so the same set of credentials are used for each, they can be overridden by adding the desired values to the system profile.

To override the username and password for the admin and robot accounts use ``portal.credentials``.

```yaml
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
```

To override the client ID and secret used for OAuth access by the robot account, use ``portal.clients``.

```yaml
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
```

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

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  workshop:
    images:
      "base-environment:*": "quay.io/eduk8s/base-environment:master"
```

It is also possible to override where images are pulled from for any arbitrary image. This could be used where you want to cache the images for a workshop in a local image registry and avoid going outside of your network, or the cluster, to get them. This means you wouldn't need to override the workshop definitions for a specific workshop to change it.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  workshop:
    images:
      "quay.io/eduk8s-labs/lab-k8s-fundamentals:master": "registry.test/lab-k8s-fundamentals:master"
```

Tracking using Google Analytics
-------------------------------

If you want to record analytics data on usage of workshops, you can enable tracking for all workshops using Google Analytics.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  analytics:
    google:
      trackingId: UA-XXXXXXX-1
```

Custom dimensions are used in Google Analytics to record details about the workshop a user is doing, and through which training portal and cluster it was accessed. You can therefore use the same Google Analytics tracking ID with eduk8s running on multiple clusters.

To support use of custom dimensions in Google Analytics you must configure the Google Analytics property with the following custom dimensions. They must be added in the order shown as Google Analytics doesn't allow you to specify the index position for a custom dimension and will allocate them for you. You can't already have custom dimensions defined for the property, as the new custom dimensions must start at index of 1.

```text
| Custom Dimension Name | Index |
|-----------------------|-------|
| workshop_name         | 1     |
| session_namespace     | 2     |
| workshop_namespace    | 3     |
| training_portal       | 4     |
| ingress_domain        | 5     |
| ingress_protocol      | 6     |
```

In addition to custom dimensions against page accesses, events are also generated. These include:

* Workshop/Start
* Workshop/Finish
* Workshop/Expired

Overriding styling of the workshop
----------------------------------

If using the REST API to create/manage workshop sessions and the workshop dashboard is then embedded into an iframe of a separate site, it is possible to perform minor styling changes of the dashboard, workshop content and portal to match the separate site. To do this you can provide CSS styles under ``theme.dashboard.style``, ``theme.workshop.style`` and ``theme.portal.style``. For dynamic styling, or for adding hooks to report on progress through a workshop to a separate service, you can also supply Javascript as part of the theme under ``theme.dashboard.script``, ``theme.workshop.script`` and ``theme.portal.script``.

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: SystemProfile
metadata:
  name: default-system-profile
spec:
  theme:
    dashboard:
      script: |
        console.log("Dashboard theme overrides.");
      style: |
        body {
          font-family: "Comic Sans MS", cursive, sans-serif;
        }
    workshop:
      script: |
        console.log("Workshop theme overrides.");
      style: |
        body {
          font-family: "Comic Sans MS", cursive, sans-serif;
        }
    portal:
      script: |
        console.log("Portal theme overrides.");
      style: |
        body {
          font-family: "Comic Sans MS", cursive, sans-serif;
        }
```

Additional custom system profiles
---------------------------------

If the default system profile is specified, it will be used by all deployments managed by the eduk8s operator unless the system profile to use has been overridden for a specific deployment. The name of the system profile can be set for deployments by setting the ``system.profile`` property of ``TrainingPortal``, ``WorkshopEnvironment`` and ``WorkshopSession`` custom resources.

```yaml
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
```
