Sample Workshop
===============

Using eduk8s there are various ways in which you could deploy and run workshops. This can be for individual learning, or for a classroom like environment if running training for many people at once. It also provides the basis for setting up and running a learning portal for on demand training.

The following sections describe the core steps for deploying a single workshop instance. The quick path to deploying a workshop for multiple users will be shown, as well as a break down of what is happening under the covers so you can see how custom deployment solutions can be developed.

Loading the workshop definition
-------------------------------

Each workshop is described by a custom resource of type ``Workshop``. Before a workshop environment can be created, the definition of the workshop must first be loaded.

To load the definition of a sample workshop, run::

    kubectl apply -f https://raw.githubusercontent.com/eduk8s-labs/lab-k8s-fundamentals/master/resources/workshop.yaml

The custom resource created is cluster scoped, and the command needs to be run as a cluster admin or other appropriate user with permission to create the resource.

If successfully loaded, the command will output::

    workshop.training.eduk8s.io/lab-k8s-fundamentals configured

You can list the workshop definitions which have been loaded, and which can be deployed by running::

    kubectl get workshops

For the sample workshop, this will output::

    NAME                   IMAGE                                             URL
    lab-k8s-fundamentals   quay.io/eduk8s-labs/lab-k8s-fundamentals:master   https://github.com/eduk8s-labs/lab-k8s-fundamentals

The additional fields provide the container image which will be deployed for the workshop, and a URL where you can find out more information about the workshop.

The definition of a workshop is loaded as a step of its own, rather than referring to a remotely hosted definition, so that a cluster admin can audit the workshop definition and ensure that it isn't doing something they don't want to allow. Once the workshop definition has been approved, then it can be used to create instances of the workshop.

Creating a workshop training room
---------------------------------

The quick path to deploying a workshop for one or more users, is to use the ``TrainingRoom`` custom resource. This custom resource specifies the workshop to be deployed, and the number of people who will be doing the workshop.

For the sample workshop run::

    kubectl apply -f https://raw.githubusercontent.com/eduk8s-labs/lab-k8s-fundamentals/master/resources/training-room.yaml

The custom resource created is cluster scoped, and the command needs to be run as a cluster admin or other appropriate user with permission to create the resource.

This will output::

    trainingroom.training.eduk8s.io/lab-k8s-fundamentals created

but there is a lot more going on under the covers than this. To see all the resources created, run::

    kubectl get eduk8s-training -o name

You should see::

    workshop.training.eduk8s.io/lab-k8s-fundamentals
    workshopsession.training.eduk8s.io/lab-k8s-fundamentals-user1
    workshopenvironment.training.eduk8s.io/lab-k8s-fundamentals
    trainingroom.training.eduk8s.io/lab-k8s-fundamentals

In addition to the original ``Workshop`` custom resource providing the definition of the workshop, and the ``TrainingRoom`` custom resource you just created, ``WorkshopEnvironment`` and ``WorkshopSession`` custom resources have also been created.

The ``WorkshopEnvironment`` custom resource sets up the environment for a workshop, including deploying any application services which need to exist and would be shared by all workshop instances.

The ``WorkshopSession`` custom resource results in the creation of a single workshop instance.

You can see a list of the workshop instances which were created, and access details by running::

    kubectl get workshopsessions

This should yield output similar to::

    NAME                         URL                                      USERNAME   PASSWORD
    lab-k8s-fundamentals-user1   http://lab-k8s-fundamentals-user1.test   eduk8s     Djiuz9Tc0M7LaIsV

Only one workshop instance was created in this case, but more could be created by setting the ``session.capacity`` field of the ``TrainingRoom`` custom resource before it was created.

At this point in time, in the case of a multi user workshop, a user would need to access the particular workshop instance they were told to use, using the URL and login credentials shown.

Note that because of the sequence that the operator processes the custom resources which are created, the first workshop instance may not be deployed immediately. The workshop instance will be deployed when the operator retries the operation, which can be up to a minute delay. The workshop instance will have been created when the URL field above shows as being populated.

Because this is the first time you have deployed the workshop, it can also take a few moments to pull down the workshop image and start.

A web portal is under development which will provide a single landing point for accessing the workshop, including self registration and allocation of a workshop instance. The URL for the web portal can be found by running::

    kubectl get trainingrooms

This should yield output similar to::

    NAME                   ENVIRONMENT            PORTAL
    lab-k8s-fundamentals   lab-k8s-fundamentals   http://lab-k8s-fundamentals.test

Deleting the workshop training room
-----------------------------------

The workshop training room is intended for running workshops with a fixed time period where all workshop instances would be deleted when complete.

To delete all workshop instances and the workshop environment, run::

    kubectl delete trainingroom/lab-k8s-fundamentals

Creating the workshop environment
---------------------------------

The ``TrainingRoom`` custom resource provides a high level mechanism for creating a workshop environment and populating it with workshop instances. When the eduk8s operator processes this custom resource, all it is doing is creating other custom resources to trigger the creation of the workshop environment and the workshop instances. If you want more control, you can use these latter custom resources directly instead.

With the definition of a workshop already in existence, the first underlying step to deploying a workshop is to create the workshop environment.

For the sample workshop, to create the workshop environment directly, run::

    kubectl apply -f https://raw.githubusercontent.com/eduk8s-labs/lab-k8s-fundamentals/master/resources/workshop-environment.yaml

This will result in a custom resource being created called ``WorkshopEnvironment``::

    workshopenvironment.training.eduk8s.io/lab-k8s-fundamentals created

The custom resource created is cluster scoped, and the command needs to be run as a cluster admin or other appropriate user with permission to create the resource.

The eduk8s operator will react to the creation of this custom resource and initialize the workshop environment.

For each distinct workshop environment, a separate namespace is created. This namespace will be used to hold the workshop instances. The namespace may also be used to provision any shared application services the workshop definition describes, which would be used across all workshop instances. Such shared application services will be automatically provisioned by the eduk8s operator when the workshop environment is created.

You can list the workshop environments which have been created by running::

    kubectl get workshopenvironments

For the sample workshop, this will output::

    NAME                   NAMESPACE              WORKSHOP               IMAGE                                             URL
    lab-k8s-fundamentals   lab-k8s-fundamentals   lab-k8s-fundamentals   quay.io/eduk8s-labs/lab-k8s-fundamentals:master   https://github.com/eduk8s-labs/lab-k8s-fundamentals

Additional fields give the name of the workshop environment, the namespace created for the workshop environment, the name of the workshop the environment was created from.

Requesting a workshop instance
------------------------------

To request a workshop instance, a custom resource of type ``WorkshopRequest`` needs to be created.

This is a namespaced resource allowing who can create them to be delegated using role based access controls. Further, in order to be able to request an instance of a specific workshop, you need to know the secret token specified in the description of the workshop environment. If necessary, raising of requests against a specific workshop environment can also be constrained to set namespaces on top of any defined RBAC rules.

For the sample workshop, run in the context of an appropriate namespace::

    kubectl apply -f https://raw.githubusercontent.com/eduk8s-labs/lab-k8s-fundamentals/master/resources/workshop-request.yaml

This should result in the output::

    workshoprequest.training.eduk8s.io/lab-k8s-fundamentals created

You can list the workshop requests in a namespace by running::

    kubectl get workshoprequests

For the sample workshop, this will output::

    NAME                   URL                                      USERNAME   PASSWORD
    lab-k8s-fundamentals   http://lab-k8s-fundamentals-cvh51.test   eduk8s     buQOgZvfHM7m

The additional fields provide the URL the workshop instance can be accessed as, as well as the username and password to provide when prompted by your web browser.

You can monitor the progress of this workshop deployment by listing the deployments in the namespace created for the workshop environment::

    kubectl get all -n lab-k8s-fundamentals

For each workshop instance a separate namespace is created for the session. This is linked to the workshop instance and will be where any applications would be deployed as part of the workshop. If the definition of the workshop includes a set of resources which should be automatically created for each session namespace, they will be created by the eduk8s operator. It is therefore possible to pre-deploy applications for each session.

Note that in this case we used ``WorkshopRequest`` where as when using ``TrainingRoom`` it created a ``WorkshopSession``. The workshop request does actually result in a ``WorkshopSession`` being created, but ``TrainingRoom`` skips the workshop request and directly creates the latter.

The purpose of having ``WorkshopRequest`` as a separate custom resource is to allow RBAC and other controls to be used to allow non cluster admins to create workshop instances.

Deleting the workshop instance
------------------------------

When you have finished with the workshop instance, you can delete it by deleting the custom resource for the workshop request::

    kubectl delete workshoprequest/lab-k8s-fundamentals

Deleting the workshop environment
---------------------------------

If you want to delete the whole workshop environment, it is recommended to first delete all workshop instances. Once this has been done, you can then delete the custom resource for the workshop environment::

    kubectl delete workshopenvironment/lab-k8s-fundamentals

If you don't delete the custom resources for the workshop requests, the workshop instances will still be cleaned up and removed when the workshop environment is removed, but the custom resources for the workshop requests will still remain and would need to be deleted separately.
