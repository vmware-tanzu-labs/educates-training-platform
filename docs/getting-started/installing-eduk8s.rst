Installing eduk8s
=================

Before you can start deploying workshops, you need to install a Kubernetes operator for eduk8s. The operator manages the setup of the environment for each workshop and deploys instances of a workshop for each person.

Kubernetes cluster requirements
-------------------------------

The eduk8s operator should be able to be deployed to any Kubernetes cluster supporting custom resource definitions and the concept of operators. The cluster must have an ingress router configured. If deploying the web based training portal, the cluster must have available persistent volumes of type ``ReadWriteOnce (RWO)``. A default storage class must have been defined so that persistent volume claims do not need to specify a storage class.

Testing of eduk8s has mainly been performed using Kubernetes 1.17. It has also been tested with OpenShift 4.3 (equivalent to Kubernetes 1.16).

You need to have cluster admin access in order to install the eduk8s operator.

Deploying the eduk8s operator
-----------------------------

To deploy the operator, run::

    kubectl apply -k "github.com/eduk8s/eduk8s-operator?ref=master"

Note that tagged versions haven't been created as yet, so this is using the latest stable version. Tagging of versions will be setup when the first official release is made.

The command above will create a namespace in your Kubernetes cluster called ``eduk8s`` and the operator along with any required namespaced resources will be created in it. A set of custom resource definitions and a global cluster role binding will also be created. The list of resources you should see being created are::

    customresourcedefinition.apiextensions.k8s.io/trainingportals.training.eduk8s.io created
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

Replace ``test`` with the domain name for your Kubernetes cluster. If you do not set this, the ingress created will use ``training.eduk8s.io`` as a default.

When running Kubernetes on your local machine using a system like ``minikube`` and you don't have a custom domain name which maps to the IP for the cluster, you can use a ``nip.io`` address.

For example, if ``minikube ip`` returned ``192.168.64.1``, you could use::

    kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_DOMAIN=192.168.64.1.nip.io
