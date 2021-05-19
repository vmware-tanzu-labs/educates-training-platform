Installing Operator
===================

Before you can start deploying workshops, you need to install a Kubernetes operator for eduk8s. The operator manages the setup of the environment for each workshop and deploys instances of a workshop for each person.

Kubernetes cluster requirements
-------------------------------

The eduk8s operator should be able to be deployed to any Kubernetes cluster supporting custom resource definitions and the concept of operators.

The cluster must have an ingress router configured. Only a basic deployment of the ingress controller is usually required. You do not need to configure the ingress controller to handle cluster wide edge termination of secure HTTP connections. Educates will create Kubernetes Ingress resources and supply any secret for use with secure HTTP connections for each ingress.

For the ingress controller we strongly recommend the use of Contour over alternatives such as nginx. An nginx based ingress controller has a less than optimal design whereby every time a new ingress is created in the cluster, the nginx config is reloaded resulting in websocket connections being terminated after a period of time. Educates terminals are implemented to reconnect automatically in the case of the websocket connection being lost, but not all applications you may use with specific workshops may handle loss of websocket connections so gracefully and so they may be impacted due to the use of an nginx ingress controller. This problem is not specific to Educates and can impact any application when using an nginx ingress controller and ingresses are created/deleted frequently.

If using a hosted Kubernetes solution from an IaaS provider such as Google, AWS or Azure, you may to ensure that any HTTP request timeout specified on the inbound load balancer for the ingress controller is increased such that long lived websocket connections can be used. Load balancers of hosted Kubernetes solutions in some cases only have a 30 second timeout. If possible configure the timeout which would apply to websockets to be 1 hour.

If deploying the web based training portal, the cluster must have available persistent volumes of type ``ReadWriteOnce (RWO)``. A default storage class should have been defined so that persistent volume claims do not need to specify a storage class. For some Kubernetes distributions, including from IBM, it may be necessary to configure Educates to know about what user and group should be used for persistent volumes. If no default storage class is specified, or a specified storage class is required, Educates can be configured with the name of the storage class.

You need to have cluster admin access in order to install the eduk8s operator.

Cluster pod security policies
-----------------------------

The eduk8s operator will define pod security policies to limit what users can do from workshops when deploying workloads to the cluster. The default policy prohibits running of images as the ``root`` user or using a privileged pod. Specified workshops may relax these restrictions and apply a policy which enables additional privileges required by the workshop.

It is highly recommended that the pod security policy admission controller be enabled for the cluster to ensure that the pod security policies are applied. If the admission controller is not enabled, users would be able to deploy workloads which run as the ``root`` user in a container, or run privileged pods.

If you are unable to enable the pod security policy admission controller, you should only provide access to workshops deployed using the eduk8s operator to users you trust.

Also note that where the pod security policy admission controller is not enabled, any workshops which have users create persistent volumes may not work, as the user the pod runs as may not have access to the volume. The pod security policy when applied usually enables access by ensuring that the security context of a pod is modified to give access.

Whether the absence of the pod security policy admission controller will cause issues with access to persistent volumes will depend on the cluster. Although minikube doesn't enable the pod security policy admission controller, it will still work as persistent volumes when mounted give write permissions to all users.

No matter whether pod security policies are enabled or not, individual workshops should always be reviewed as to what additional privileges they grant before allowing their use in a cluster.

Creating the operator deployment
--------------------------------

To deploy the operator, run:

```
kubectl apply -k "github.com/eduk8s/eduk8s?ref=master"
```

The command above will create a namespace in your Kubernetes cluster called ``eduk8s`` and the operator along with any required namespaced resources will be created in it. A set of custom resource definitions and a global cluster role binding will also be created. The list of resources you should see being created are:

```
customresourcedefinition.apiextensions.k8s.io/workshops.training.eduk8s.io created
customresourcedefinition.apiextensions.k8s.io/workshopsessions.training.eduk8s.io created
customresourcedefinition.apiextensions.k8s.io/workshopenvironments.training.eduk8s.io created
customresourcedefinition.apiextensions.k8s.io/workshoprequests.training.eduk8s.io created
customresourcedefinition.apiextensions.k8s.io/trainingportals.training.eduk8s.io created
serviceaccount/eduk8s created
customresourcedefinition.apiextensions.k8s.io/systemprofiles.training.eduk8s.io created
clusterrolebinding.rbac.authorization.k8s.io/eduk8s-cluster-admin created
deployment.apps/eduk8s-operator created
```

You can check that the operator deployed okay by running:

```
kubectl get all -n eduk8s
```

The pod for the operator should be marked as running.

Pinning to a specific version
-----------------------------

The example command given above deploys from the ``master`` branch of the ``eduk8s/eduk8s`` repository on GitHub. This means that the most up to date official version available at the time will be deployed. If at some later time a new version had been released and you ran the same deployment command again, the version of the installed operator would be upgraded.

If you want to pin your deployment of the operator to a specific version, visit the page:

* [https://github.com/eduk8s/eduk8s/releases](https://github.com/eduk8s/eduk8s/releases)

and identify a version that you want to install. Use that version number in place of ``master`` as the repository reference in the installation command:

```
kubectl apply -k "github.com/eduk8s/eduk8s?ref=20.05.11.1"
```

Tagged version numbers used by the ``eduk8s/eduk8s`` repository follow `CalVer <https://calver.org/>`_, specifically the format ``YY.0M.0D.MICRO``. The ``MICRO`` component is an incrementing integer used where more than one release were performed in single day.

The complete eduk8s training environment combines components from numerous different repositories and images. These all follow their own separate version conventions. CalVer is again used for those, but they use the format ``YYMMDD.HHMMSS.MICRO`` where ``MICRO`` is the short SHA-1 git repository reference of the commit the tag is against.

Specifying the ingress domain
-----------------------------

The operator when deploying instances of the workshop environments needs to be able to expose them via an external URL for access. To define the domain name that can be used as a suffix to hostnames for instances, you can set the ``INGRESS_DOMAIN`` environment variable on the operator deployment. To do this run:

```
kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_DOMAIN=test
```

Replace ``test`` with the domain name for your Kubernetes cluster. If you do not set this, the ingress created will use ``training.eduk8s.io`` as a default.

Note that use of environment variables to configure the operator is a short cut to cater for the simple use case. For more complicated scenarios the ``SystemProfile`` custom resource should be used.

For the custom domain you are using, DNS must have been configured with a wildcard domain to forward all requests for sub domains of the custom domain, to the ingress router of the Kubernetes cluster.

It is recommended that you avoid using a ``.dev`` domain name as such domain names have a requirement to always use HTTPS and you cannot use HTTP. Although you can provide a certificate for secure connections under the domain name for use by Educates, this doesn't extend to what a workshop may do. By using a ``.dev`` domain name, if workshop instructions have you creating ingresses in Kubernetes using HTTP only, they will not work.

If you are running Kubernetes on your local machine using a system like ``minikube`` and you don't have a custom domain name which maps to the IP for the cluster, you can use a ``nip.io`` address.

For example, if ``minikube ip`` returned ``192.168.64.1``, you could use:

```
kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_DOMAIN=192.168.64.1.nip.io
```

Note that you cannot use an address of form ``127.0.0.1.nip.io``, or ``subdomain.localhost``. This will cause a failure as internal services when needing to connect to each other, would end up connecting to themselves instead, since the address would resolve to the host loopback address of ``127.0.0.1``.

If you are using OpenShift Code Ready Containers, then you would set the ingress domain to be ``apps-crc.testing``

Enforcing secure connections
----------------------------

By default the workshop portal and workshop sessions will be accessible over HTTP connections. If you wish to use secure HTTPS connections, you must have access to a wildcard SSL certificate for the domain under which you wish to host the workshops. You cannot use a self signed certificate.

Wildcard certificates can be created using `letsencrypt <https://letsencrypt.org/>`_. Once you have the certificate, add it as a secret in the ``eduk8s`` namespace. The secret needs to be of type ``tls``. You can create it using the ``kubectl create secret tls`` command.

```
kubectl create secret tls -n eduk8s training.eduk8s.io-tls --cert=training.eduk8s.io/fullchain.pem --key=training.eduk8s.io/privkey.pem
```

Having created the secret, if it is the secret corresponding to the default ingress domain you specified above, set the ``INGRESS_SECRET`` environment variable on the operator deployment. This will ensure that it is applied automatically to any ingress created.

```
kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_SECRET=training.eduk8s.io-tls
```

If the certificate isn't that of the default ingress domain, you can supply the domain name and name of the secret when creating a workshop environment or training portal. In either case, secrets for the wildcard certificates must be created in the ``eduk8s`` namespace.

Specifying the ingress class
----------------------------

Any ingress routes created will use the default ingress class. If you have multiple ingress class types available, and you need to override which is used, you can set the ``INGRESS_CLASS`` environment variable for the eduk8s operator.

```
kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_CLASS=nginx
```

This only applies to the ingress created for the training portal and workshop sessions. It does not apply to the any ingress created from a workshop as part of the workshop instructions.

This may be necessary where a specific ingress provider is not as reliable in maintaining the websocket connections used by the workshop terminals.

Trusting insecure registries
----------------------------

One of the options available for workshops is to automatically deploy an image registry per workshop session. When the eduk8s operator is configured to use a secure ingress with valid wildcard certificate, the image registry will work out of the box.

If the eduk8s operator is not setup to use secure ingress, the image registry will be accessed over HTTP and will be regarded as an insecure registry.

When using the optional support for building container images using ``docker``, the docker daemon deployed for the workshop session will be configured in this case so it knows the image registry is insecure and pushing images to the image registry will still work.

In this case of an insecure image registry, deployment of images from the image registry to the Kubernetes cluster will not however work unless the Kubernetes cluster is configured to trust the insecure registry.

How you configure a Kubernetes cluster to trust an insecure image registry will differ based on how the Kubernetes cluster is deployed and what container runtime it uses.

If you are using ``minikube`` with ``dockerd``, to ensure that the image registry is trusted, you will need to set up the trust the very first time you create the minikube instance.

To do this, first determine which IP subnet minikube uses for the inbound ingress router of the cluster. If you already have a minikube instance running, you can determine this by running ``minikube ip``. If for example this reported ``192.168.64.1``, the subnet used is ``129.168.64.0/24``.

With this information, when you create a fresh ``minikube`` instance you would supply the ``--insecure-registry`` option with the subnet.

```
minikube start --insecure-registry="129.168.64.0/24"
```

What this option will do is tell ``dockerd`` to regard any image registry as insecure, which is deployed in the Kubernetes cluster, and which is accessed via a URL exposed via an ingress route of the cluster itself.

Note that at this time there is no known way to configure ``containerd`` to treat image registries matching a wildcard subdomain, or which reside in a subnet, as insecure. It is therefore not possible to run workshops which need to deploy images from the per session image registry when using ``containerd`` as the underlying Kubernetes cluster container runtime. This is a limitation of ``containerd`` and there are no known plans for ``containerd`` to support this ability. This will limit your ability to use Kubernetes clusters deployed with a tool like ``kind``, which relies on using ``containerd``.
