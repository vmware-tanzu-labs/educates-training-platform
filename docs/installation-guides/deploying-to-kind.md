Deploying to Kind
=================

Kind was developed as a means to support development and testing of Kubernetes. Despite it existing primarily for that purpose, Kind clusters are often used for local development of user applications as well. For Educates, a local Kind cluster can be used for developing workshop content, or for self learning when deploying other peoples workshops.

As you are deploying to a local machine you are unlikely to have access to your own custom domain name and certificate you can use with the cluster. If you don't, you will be restricted as to the sorts of workshops you can develop or run using Educates in Kind. This is because Kind uses containerd and containerd lacks certain features that allows one to trust any image registries hosted within a subnet. This means you cannot run workshops which use a local image registry for each workshop session.

Also keep in mind that since Kind generally has limited memory resources available you may be prohibited from running workshops which have large memory requirements. Certain workshops which demonstrate use of third party applications requiring a multi node cluster will also not work unless the Kind cluster is specifically configured to be multi node rather than a single node.

Requirements and setup instructions specific to Kind are detailed below, otherwise normal installation instructions for the Educates operator should be followed.

Ingress controller with DNS
---------------------------

When initially creating the Kind cluster you will need to [configure](https://kind.sigs.k8s.io/docs/user/ingress#create-cluster) it so that the ingress controller will be exposed. Once the Kind cluster is running, you then need to install an ingress controller.

The Kind documentation provides instructions for installing Ambassador, Contour and Nginx based ingress controllers.

It is recommended that [Contour](https://kind.sigs.k8s.io/docs/user/ingress#contour) be used rather than Nginx, as the latter will drop web socket connections whenever new ingresses are created. The Educates workshop environments do include a workaround to re-establish websocket connections for the workshop terminals without loosing terminal state, but other applications used with workshops may not, such as terminals available through VS Code.

You should avoid using the Ambassador ingress controller as it requires all ingresses created to be annotated explictly with an ingress class of "ambassador". The Educates operator can be configured to do this automatically for ingresses created for the training portal and workshop sessions, but any workshops which create ingresses as part of the workshop instructions will not work unless they are written to have the user manually add the ingress class when required due to the use of Ambassador.

Using a nip.io DNS address
--------------------------

Once the Educates operator is installed, before you can start deploying workshops, you need to configure the operator to tell it what domain name can be used to access anything deployed by the operator.

Being a local cluster which isn't exposed to the internet with its own custom domain name, you can use a [nip.io](
https://nip.io/). address.

To calculate the ``nip.io`` address to use, first work out the IP address for the ingress controller exposed by Kind. This is usually the IP address of the local machine itself, even where you may be using Docker for Mac.

How you get the IP address for your local machine depends on the operating system being used.

Once you have the IP address, if for example it was ``192.168.1.1``, use the domain name of ``192.168.1.1.nip.io``.

To configure the Educates operator with this cluster domain, run:

```
kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_DOMAIN=192.168.1.1.nip.io
```

This will cause the Educates operator to automatically be re-deployed with the new configuration.

You should now be able to start deploying workshops.

Note that some home internet gateways implement what is called rebind protection. That is, they will not let DNS names from the public internet bind to local IP address ranges inside of the home network. If your home internet gateway has such a feature and it is enabled, it will block ``nip.io`` addresses from working. In this case you will need to configure your home internet gateway to allow ``*.nip.io`` names to be bound to local addresses.

Also note that you cannot use an address of form ``127.0.0.1.nip.io``, or ``subdomain.localhost``. This will cause a failure as internal services when needing to connect to each other, would end up connecting to themselves instead, since the address would resolve to the host loopback address of ``127.0.0.1``.
