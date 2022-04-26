Workshop Environment
====================

The ``WorkshopEnvironment`` custom resource defines a workshop environment.

The raw custom resource definition for the ``WorkshopEnvironment`` custom resource can be viewed at:

```
kubectl get crd/workshopenvironments.training.educates.dev -o yaml
```

Specifying the workshop definition
----------------------------------

The creation of a workshop environment is performed as a separate step to loading the workshop definition. This is to allow multiple distinct workshop environments using the same workshop definition to be created if necessary.

To specify which workshop definition is to be used for a workshop environment, set the ``workshop.name`` field of the specification for the workshop environment.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
```

The ``name`` of the workshop environment specified in the ``metadata`` of the workshop environment does not need to be the same, and has to be different if creating multiple workshop environments from the same workshop definition.

When the workshop environment is created, the namespace created for the workshop environment will use the ``name`` of the workshop environment specified in the ``metadata``. This name will also be used in the unique names of each workshop instance created under the workshop environment.

Overriding environment variables
--------------------------------

A workshop definition may specify a list of environment variables that need to be set for all workshop instances. If you need to override an environment variable specified in the workshop definition, or one which is defined in the container image, you can supply a list of environment variables as ``session.env``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  session:
    env:
    - name: REPOSITORY_URL
      value: https://github.com/vmware-tanzu-labs/lab-markdown-sample
```

You might use this to set the location of a backend service, such as an image registry, to be used by the workshop.

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``session_id`` - A unique ID for the workshop instance within the workshop environment.
* ``session_namespace`` - The namespace created for and bound to the workshop instance. This is the namespace unique to the session and where a workshop can create their own resources.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances are created, and where the service account that the workshop instance runs as exists.
* ``service_account`` - The name of the service account the workshop instance runs as, and which has access to the namespace created for that workshop instance.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

The syntax for referencing one of the parameters is ``$(parameter_name)``.

Overriding the ingress domain
-----------------------------

In order to be able to access a workshop instance using a public URL, you will need to specify an ingress domain. If an ingress domain isn't specified, the default ingress domain that the Educates operator has been configured with will be used.

When setting a custom domain, DNS must have been configured with a wildcard domain to forward all requests for sub domains of the custom domain, to the ingress router of the Kubernetes cluster.

To provide the ingress domain, you can set the ``session.ingress.domain`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  session:
    ingress:
      domain: training.educates.dev
```

If overriding the domain, by default, the workshop session will be exposed using a HTTP connection. If you require a secure HTTPS connection, you will need to have access to a wildcard SSL certificate for the domain. A secret of type ``tls`` should be created for the certificate in the ``eduk8s`` namespace. The name of that secret should then be set in the ``session.ingress.secret`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  session:
    ingress:
      domain: training.educates.dev
      secret: training.educates.dev-tls
```

If HTTPS connections are being terminated using an external load balancer and not by specificying a secret for ingresses managed by the Kubernetes ingress controller, with traffic then routed into the Kubernetes cluster as HTTP connections, you can override the ingress protocol without specifying an ingress secret by setting the ``session.ingress.protocol`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  session:
    ingress:
      domain: training.educates.dev
      protocol: https
```

If you need to override or set the ingress class, which dictates which ingress router is used when more than one option is available, you can add ``session.ingress.class``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  session:
    ingress:
      domain: training.educates.dev
      secret: training.educates.dev-tls
      class: nginx
```

Controlling access to the workshop
----------------------------------

By default, the ability to request a workshop using the ``WorkshopRequest`` custom resource is disabled and so must be enabled for a workshop environment by setting ``request.enabled`` to ``true``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  request:
    enabled: true
```

With this enabled, anyone able to create a ``WorkshopRequest`` custom resource could request the creation of a workshop instance for the workshop environment.

To further control who can request a workshop instance in the workshop environment, you can first set an access token, which a user would need to know and supply with the workshop request. This can be done by setting the ``request.token`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  request:
    enabled: true
    token: lab-markdown-sample
```

In this example the same name as the workshop environment is used, which is probably not a good practice. Use a random value instead. The token value can be multiline if desired.

As a second measure of control, you can specify what namespaces the ``WorkshopRequest`` needs to be created in to be successful. This means a user would need to have the specific ability to create ``WorkshopRequest`` resources in one of those namespaces.

The list of namespaces from which workshop requests for the workshop environment is allowed can be specified by setting ``request.namespaces``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  request:
    enabled: true
    token: lab-markdown-sample
    namespaces:
    - default
```

If you want to add the workshop namespace in the list, rather than list the literal name, you can reference a predefined parameter specifying the workshop namespace by including ``$(workshop_namespace)``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  request:
    enabled: true
    token: lab-markdown-sample
    namespaces:
    - $(workshop_namespace)
```

Overriding the login credentials
--------------------------------

When requesting a workshop using ``WorkshopRequest``, a login prompt for the workshop instance will be presented to a user when the URL for the workshop instance is accessed. By default the username they need to use will be ``eduk8s``. The password will be a random value which they need to query from the ``WorkshopRequest`` status after the custom resource has been created.

If you want to override the username, you can specify the ``session.username`` field. If you want to set the same fixed password for all workshop instances, you can specify the ``session.password`` field.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  session:
    username: workshop
    password: lab-markdown-sample
```

Additional workshop resources
-----------------------------

The workshop definition defined by the ``Workshop`` custom resource already declares a set of resources to be created with the workshop environment. This could be used when you have shared service applications needed by the workshop, such as an image registry, or a Git repository server.

If you need to deploy additional applications related to a specific workshop environment, you can declare them by adding them into the ``environment.objects`` field of the ``WorkshopEnvironment`` custom resource. You might use this deploy a web application used by attendees of a workshop to access their workshop instance.

For namespaced resources, it is not necessary to specify the ``namespace`` field of the resource ``metadata``. When the ``namespace`` field is not present the resource will automatically be created within the workshop namespace for that workshop environment.

When resources are created, owner references are added making the ``WorkshopEnvironment`` custom resource corresponding to the workshop environment the owner. This means that when the workshop environment is deleted, any resources will be automatically deleted.

Values of fields in the list of resource objects can reference a number of pre-defined parameters. The available parameters are:

* ``workshop_name`` - The name of the workshop. This is the name of the ``Workshop`` definition the workshop environment was created against.
* ``environment_name`` - The name of the workshop environment. For now this is the same as the name of the namespace for the workshop environment. Don't rely on them being the same, and use the most appropriate to cope with any future change.
* ``environment_token`` - The value of the token which needs to be used in workshop requests against the workshop environment.
* ``workshop_namespace`` - The namespace for the workshop environment. This is the namespace where all deployments of the workshop instances, and their service accounts, are created. It is the same namespace that shared workshop resources are created.
* ``service_account`` - The name of a service account that can be used when creating deployments in the workshop namespace.
* ``ingress_domain`` - The host domain under which hostnames can be created when creating ingress routes.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.
* ``ingress_secret`` - The name of the ingress secret stored in the workshop namespace when secure ingress is being used.

If you want to create additional namespaces associated with the workshop environment, embed a reference to ``$(workshop_namespace)`` in the name of the additional namespaces, with an appropriate suffix. Be mindful that the suffix doesn't overlap with the range of session IDs for workshop instances.

When creating deployments in the workshop namespace, set the ``serviceAccountName`` of the ``Deployment`` resouce to ``$(service_account)``. This will ensure the deployment makes use of a special pod security policy set up by Educates. If this isn't used and the cluster imposes a more strict default pod security policy, your deployment may not work, especially if any image expects to run as ``root``.

Creation of workshop instances
------------------------------

Once a workshop environment has been created you can create the workshop instances. A workshop instance can be requested using the ``WorkshopRequest`` custom resource. This can be done as a separate step, or you can use the trick of adding them as resources under ``environment.objects``.

```yaml
apiVersion: training.educates.dev/v1beta1
kind: WorkshopEnvironment
metadata:
  name: lab-markdown-sample
spec:
  workshop:
    name: lab-markdown-sample
  request:
    token: lab-markdown-sample
    namespaces:
    - $(workshop_namespace)
  session:
    username: eduk8s
    password: lab-markdown-sample
  environment:
    objects:
    - apiVersion: training.educates.dev/v1beta1
      kind: WorkshopRequest
      metadata:
        name: user1
      spec:
        environment:
          name: $(environment_name)
          token: $(environment_token)
    - apiVersion: training.educates.dev/v1beta1
      kind: WorkshopRequest
      metadata:
        name: user2
      spec:
        environment:
          name: $(environment_name)
          token: $(environment_token)
```

Using this method, the workshop environment will be automatically populated with workshop instances. You will need to query the workshop requests from the workshop namespace to determine the URLs for accessing each, and the password if you didn't set one and a random password was assigned.

If you needed more control over how the workshop instances were created using this method, you could use the ``WorkshopSession`` custom resource instead.
