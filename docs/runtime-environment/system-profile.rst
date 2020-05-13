.. _system-profile-resource:

System Profile
==============

The ``SystemProfile`` custom resource is used to configure the eduk8s operator. The default system profile can be used to set defaults for ingress and image pull secrets, with specific deployments being able to select an alternate profile if required.

The raw custom resource definition for the ``SystemProfile`` custom resource can be viewed at:

* https://github.com/eduk8s/eduk8s-operator/blob/develop/resources/crds-v1/system-profile.yaml

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

In addition to details for the ingress, the system profiles can define lists of image pull secrets that should be added to the service accounts used to deploy and run the workshop images. This can be used to provide access to workshop images stored in a private image registry deployed in the cluster or hosted externally. The ``environment.secrets.pull`` property should be set to the list of secret names.

.. code-block:: yaml
    :emphasize-lines: 10-14

    apiVersion: training.eduk8s.io/v1alpha1
    kind: SystemProfile
    metadata:
      name: default-system-profile
    spec:
      ingress:
        domain: training.eduk8s.io
        secret: training-eduks8-io-tls
        class: nginx
      environment:
        secrets:
          pull:
          - cluster-image-registry-pull
          - external-image-registry-pull

The secrets containing the image registry credentials must exist within the ``eduk8s`` namespace where the eduk8s operator is deployed. The secret resources must be of type ``kubernetes.io/dockerconfigjson``.

Note that this doesn't result in any secrets being added to the namespace created for each workshop session. The secrets are only added to the workshop namespace and are not visible to a user.

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
      portal:
        capacity: 1
      workshops:
      - name: lab-markdown-sample
