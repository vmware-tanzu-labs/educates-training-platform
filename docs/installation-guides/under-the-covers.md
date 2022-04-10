Under the Covers
================

The ``TrainingPortal`` custom resource provides a high level mechanism for creating a set of workshop environments and populating it with workshop instances. When the eduk8s operator processes this custom resource, all it is doing is creating other custom resources to trigger the creation of the workshop environment and the workshop instances. If you want more control, you can use these latter custom resources directly instead.

Creating the workshop environment
---------------------------------

With the definition of a workshop already in existence, the first underlying step to deploying a workshop is to create the workshop environment.

To create the workshop environment run:

```
kubectl apply -f https://raw.githubusercontent.com/eduk8s-labs/lab-k8s-fundamentals/master/resources/workshop-environment.yaml
```

This will result in a custom resource being created called ``WorkshopEnvironment``:

```
workshopenvironment.training.eduk8s.io/lab-k8s-fundamentals created
```

The custom resource created is cluster scoped, and the command needs to be run as a cluster admin or other appropriate user with permission to create the resource.

The eduk8s operator will react to the creation of this custom resource and initialize the workshop environment.

For each distinct workshop environment, a separate namespace is created. This namespace will be used to hold the workshop instances. The namespace may also be used to provision any shared application services the workshop definition describes, which would be used across all workshop instances. Such shared application services will be automatically provisioned by the eduk8s operator when the workshop environment is created.

You can list the workshop environments which have been created by running:

```
kubectl get workshopenvironments
```

This will output:

```
NAME                       WORKSHOP               URL   STATUS
lab-k8s-fundamentals-w01   lab-k8s-fundamentals         Running
```

Additional fields give the name of the workshop environment, the namespace created for the workshop environment, and the name of the workshop the environment was created from.

Requesting a workshop instance
------------------------------

To request a workshop instance, a custom resource of type ``WorkshopRequest`` needs to be created.

This is a namespaced resource allowing who can create them to be delegated using role based access controls. Further, in order to be able to request an instance of a specific workshop, you need to know the secret token specified in the description of the workshop environment. If necessary, raising of requests against a specific workshop environment can also be constrained to a specific set of namespaces on top of any defined RBAC rules.

In the context of an appropriate namespace, run:

```
kubectl apply -f https://raw.githubusercontent.com/eduk8s-labs/lab-k8s-fundamentals/master/resources/workshop-request.yaml
```

This should result in the output:

```
workshoprequest.training.eduk8s.io/lab-k8s-fundamentals created
```

You can list the workshop requests in a namespace by running:

```
kubectl get workshoprequests
```

This will display output similar to:

```
NAME                   URL                                      USERNAME   PASSWORD
lab-k8s-fundamentals   http://lab-k8s-fundamentals-cvh51.test   eduk8s     buQOgZvfHM7m
```

The additional fields provide the URL the workshop instance can be accessed as, as well as the username and password to provide when prompted by your web browser.

Note that the user name and password only come into play when you use the lower level resources to setup workshops. If you use the ``TrainingPortal`` custom resource, you will see that these fields are empty. This is because for that case, the workshop instances are deployed in a way that they rely on user registration and access mediated by the web based training portal. Visiting the URL for a workshop instance directly when using ``TrainingPortal`` will redirect you back to the web portal in or order to login if necessary.

You can monitor the progress of this workshop deployment by listing the deployments in the namespace created for the workshop environment:

```
kubectl get all -n lab-k8s-fundamentals
```

For each workshop instance a separate namespace is created for the session. This is linked to the workshop instance and will be where any applications would be deployed as part of the workshop. If the definition of the workshop includes a set of resources which should be automatically created for each session namespace, they will be created by the eduk8s operator. It is therefore possible to pre-deploy applications for each session.

Note that in this case we used ``WorkshopRequest`` where as when using ``TrainingPortal`` it created a ``WorkshopSession``. The workshop request does actually result in a ``WorkshopSession`` being created, but ``TrainingPortal`` skips the workshop request and directly creates the latter.

The purpose of having ``WorkshopRequest`` as a separate custom resource is to allow RBAC and other controls to be used to allow non cluster admins to create workshop instances.

Deleting the workshop instance
------------------------------

When you have finished with the workshop instance, you can delete it by deleting the custom resource for the workshop request:

```
kubectl delete workshoprequest/lab-k8s-fundamentals
```

Deleting the workshop environment
---------------------------------

If you want to delete the whole workshop environment, it is recommended to first delete all workshop instances. Once this has been done, you can then delete the custom resource for the workshop environment:

```
kubectl delete workshopenvironment/lab-k8s-fundamentals
```

If you don't delete the custom resources for the workshop requests, the workshop instances will still be cleaned up and removed when the workshop environment is removed, but the custom resources for the workshop requests will still remain and would need to be deleted separately.
