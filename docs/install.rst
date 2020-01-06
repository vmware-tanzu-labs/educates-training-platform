Installing eduk8s
=================

Before you can start deploying workshops, you need to install a Kubernetes operator for eduk8s. The operator manages the setup of the environment for each workshop and deploys instances of a workshop for each person.

Deploying the eduk8s operator
-----------------------------

To deploy the operator, run::

    kubectl apply -k github.com/eduk8s/eduk8s-operator?ref=master

Note that tagged versions haven't been created as yet, so this is using the latest version. Tagging of versions will be setup soon.

The command above will create a namespace in your Kubernetes cluster called ``eduk8s`` and the operator along with any required namespaced resources will be created in it. A set of custom resource definitions and a global cluster role binding will also be created. The list of resources you should see being created are::

    customresourcedefinition.apiextensions.k8s.io/workshopenvironments.training.eduk8s.io created
    customresourcedefinition.apiextensions.k8s.io/workshoprequests.training.eduk8s.io created
    customresourcedefinition.apiextensions.k8s.io/workshops.training.eduk8s.io created
    customresourcedefinition.apiextensions.k8s.io/workshopsessions.training.eduk8s.io created
    serviceaccount/eduk8s created
    clusterrolebinding.rbac.authorization.k8s.io/eduk8s-cluster-admin created
    deployment.apps/eduk8s-operator created

You can check that the operator deployed okay by running::

    kubectl get all -n eduk8s

The pod for the operator should be marked as running.

Specifying the ingress domain
-----------------------------

The operator when deploying instances of the workshop environments needs to be able to expose them via an external URL for access. To define the domain name that can be used as a suffix to hostnames for instances, you need to set the ``INGRESS_DOMAIN`` environment variable on the operator deployment. To do this run::

    kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_DOMAIN=test

Replace ``test`` with the domain name for your Kubernetes cluster.

If you do not set this, the ingress created will use ``training.eduk8s.io`` as a default.

If your Kubernetes cluster doesn't have an ingress controller configured, you will need to use port forwarding to access a workshop environment.
