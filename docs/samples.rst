Sample Workshop
===============

Using eduk8s there are various ways in which you could deploy and run workshops. This can be for individual learning, or for a classroom like environment if running training for many people at once. It also provides the basis for setting up and running a learning portal for on demand training.

The following sections describe the core steps for deploying a single workshop instance. Other methods for deployment build on these basic steps and will be described elsewhere in the documentation.

Loading the workshop definition
-------------------------------

Each workshop is described by a custom resource of type ``workshop``. Before a workshop environment can be created, the definition of the workshop must first be loaded.

To load the definition of a sample workshop, run::

    kubectl apply -f https://raw.githubusercontent.com/eduk8s/lab-markdown-sample/master/resources/workshop.yaml

The custom resource created is cluster scoped, and the command needs to be run as a cluster admin or other appropriate user with permission to create the resource.

If successfully loaded, the command will output::

    workshop.training.eduk8s.io/lab-markdown-sample created

You can list the workshop definitions which have been loaded, and which can be deployed by running::

    kubectl get workshops

For the sample workshop, this will output::

    NAME                  IMAGE
    lab-markdown-sample   quay.io/eduk8s/lab-markdown-sample:master

The name of the workshop and the container image for the workshop will be listed. If you run::

    kubectl get workshops -o wide

additional fields will be displayed, including the URL where you can find more information about the workshop::

    NAME                  IMAGE                                       URL
    lab-markdown-sample   quay.io/eduk8s/lab-markdown-sample:master   https://github.com/eduk8s/lab-markdown-sample

Creating the workshop environment
---------------------------------

When you load the definition of a workshop, only the ``workshop`` custom resource is created. Before you can starting creating workshop instances, you need to first initialize the workshop environment.

For the sample workshop run::

     kubectl apply -f https://raw.githubusercontent.com/eduk8s/lab-markdown-sample/master/resources/environment.yaml

This will result in a custom resource being created called ``workshopenvironment``::

    workshopenvironment.training.eduk8s.io/lab-markdown-sample created

The custom resource created is cluster scoped, and the command needs to be run as a cluster admin or other appropriate user with permission to create the resource.

The eduk8s operator will react to the creation of this custom resource and initialize the workshop environment.

For each distinct workshop environment, a separate namespace is created. This namespace will be used to hold the workshop instances. The namespace may also be used to provision any shared application services the workshop definition describes, which would be used across all workshop instances. Such shared application services will be automatically provisioned by the eduk8s operator when the workshop environment is created.

You can list the workshop environments which have been created by running::

    kubectl get workshopenvironments

For the sample workshop, this will output::

    NAME                  NAMESPACE             IMAGE
    lab-markdown-sample   lab-markdown-sample   quay.io/eduk8s/lab-markdown-sample:master

This gives the name of the workshop environment, the namespace created for the workshop environment, and the container image which will be used when creating the workshop instances.

Requesting a workshop instance
------------------------------

To request a workshop instance, a custom resource of type ``workshoprequest`` needs to be created.

This is a namespaced resource allowing who can create them to be delegated using role based access controls. Further, in order to be able to request an instance of a specific workshop, you need to know the secret token specified in the description of the workshop environment. If necessary, raising of requests against a specific workshop environment can also be constrained to set namespaces on top of any defined RBAC rules.

For the sample workshop, run in the context of an appropriate namespace::

    kubectl apply -f https://raw.githubusercontent.com/eduk8s/lab-markdown-sample/master/resources/request.yaml

This should result in the output::

    workshoprequest.training.eduk8s.io/lab-markdown-sample created

You can list the workshop requests in a namespace by running::

    kubectl get workshoprequests

For the sample workshop, this will output::

    NAME                  URL                                     USERNAME   PASSWORD
    lab-markdown-sample   http://lab-markdown-sample-jkwb4.test   eduk8s     DcbrEp8sjOtL

This will output a list including your workshop request, with the URL it can be accessed as, and the username and password to provide when prompted by your web browser.

Because this is the first time you have deployed the workshop, it can take a few moments to pull down the workshop image and start. You can monitor the progress of this workshop deployment by running::

    kubectl get all -n lab-markdown-sample

For each workshop instance a separate namespace is created for the session. This is linked to the workshop instance and will be where any applications would be deployed as part of the workshop. If the definition of the workshop includes a set of resources which should be automatically created for each session namespace, the will be created by the eduk8s operator. It is therefore possible to pre-deploy applications for each session.

Deleting the workshop instance
------------------------------

When you have finished with the workshop instance, you can delete it by deleting the custom resource::

    kubectl delete workshoprequest/lab-markdown-sample

Deleting the workshop environment
---------------------------------

If you want to delete the whole workshop environment, it is recommended to first delete all workshop instances. Once this has been done, you can then delete the custom resource for the workshop environment::

    kubectl delete workshopenvironment/lab-markdown-sample

If you don't delete the custom resources for the workshop requests, the workshop instances will still be cleaned up and removed when the workshop environment is removed, but the custom resources for the workshop requests will still remain and would need to be deleted later.
