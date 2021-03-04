Deploying to Minikube
=====================

Minikube makes for a simple local deployment of Kubernetes for developing workshop content, or for self learning when deploying other peoples workshops.

As you are deploying to a local machine you are unlikely to have access to your own custom domain name and certificate you can use with the cluster, so some extra steps are required over a standard install of Minikube to ensure certain types of workshops can be run.

Also keep in mind that since Minikube generally has limited memory resources available, and is only a single node cluster, you may be prohibited from running workshops which have large memory requirements, or which demonstrate use of third party applications which require a multi node cluster.

Requirements and setup instructions specific to Minikube are detailed below, otherwise normal installation instructions for the eduk8s operator should be followed.

Trusting insecure registries
----------------------------

Workshops may optionally deploy an image registry for a workshop session. This image registry is secured with a password specific to the workshop session and is exposed via a Kubernetes ingress so it can be accessed from the workshop session.

When using Minikube, the typical scenario will be that insecure ingress routes are always going to be used. Even if you were to generate a self signed certificate to use for ingress, it will not be trusted by the ``dockerd`` that runs within Minikube. This means you have to tell Minikube to trust any insecure registry running inside of Minikube.

Configuring Minikube to trust insecure registries must be done the first time you start a new cluster with it. That is, you must supply the details to ``minikube start``. To do this you need to know the IP subnet that Minikube uses.

If you already have a cluster running using Minikube, you can run ``minikube ip`` to determine the IP address it used, and from that determine what subnet you need to tell it to trust.

For example, if ``minikube ip`` returned ``192.168.64.1``, the subnet you need to trust is ``192.168.64.0/24``.

With this information, when you start a new cluster with Minikube, you would run:

```
minikube start --insecure-registry=192.168.64.0/24
```

If you already have a cluster started with Minikube, you cannot stop it, and then provide this option when it is restarted. The option is only used for a completely new cluster.

Note that you must be using ``dockerd``, and not ``containerd``, in the Minikube cluster. This is because ``containerd`` does not accept an IP subnet when defining insecure registries to be trusted, allowing only specific hosts or IP addresses. Because though you don't know what IP address will be used by Minikube in advance, you can't provide the IP on the command line when starting Minikube to create the cluster the first time.

Ingress controller with DNS
---------------------------

Once the Minikube cluster is running, you must enable the ``ingress`` and ``ingress-dns`` addons for Minikube. These deploy the nginx ingress controller, along with support for integrating into DNS.

To enable these after the cluster has been created, run:

```
minikube addons enable ingress
minikube addons enable ingress-dns
```

You are ready now to install the eduk8s operator.

Note that the ingress addons for Minikube do not work when using Minikube on top of Docker for Mac, or Docker for Windows. On macOS you must use the Hyperkit VM driver. On Windows you must use the Hyper-V VM driver.

Using a nip.io DNS address
--------------------------

Once the eduk8s operator is installed, before you can start deploying workshops, you need to configure the operator to tell it what domain name can be used to access anything deployed by the operator.

Being a local cluster which isn't exposed to the internet with its own custom domain name, you can use a `nip.io
<https://nip.io/>`_. address.

To calculate the ``nip.io`` address to use, first work out the IP address of the cluster created by Minikube by running ``minikube ip``. This is then added as a prefix to the domain name ``nip.io``.

For example, if ``minikube ip`` returns ``192.168.64.1``, use the domain name of ``192.168.64.1.nip.io``.

To configure the eduk8s operator with this cluster domain, run:

```
kubectl set env deployment/eduk8s-operator -n eduk8s INGRESS_DOMAIN=192.168.64.1.nip.io
```

This will cause the eduk8s operator to automatically be re-deployed with the new configuration.

You should now be able to start deploying workshops.

Note that some home internet gateways implement what is called rebind protection. That is, they will not let DNS names from the public internet bind to local IP address ranges inside of the home network. If your home internet gateway has such a feature and it is enabled, it will block ``nip.io`` addresses from working. In this case you will need to configure your home internet gateway to allow ``*.nip.io`` names to be bound to local addresses.

Working with large images
-------------------------

If you are creating or running workshops which work with the image registry created for a workshop session, and you are going to be pushing images to that image registry which have very large layers in them, you will need to configure the version of nginx deployed for the ingress controller and increase the allowed size of request data for a HTTP request.

To do this run:

```
kubectl edit configmap nginx-load-balancer-conf -n kube-system
```

To the config map resource add the following property under ``data``:

```
proxy-body-size: 1g
```

If you don't increase this you will find ``docker push`` failing when trying to push container images with very large layers.

Limited resource availability
-----------------------------

By default Minikube when deploying a cluster only configures support for 2Gi of memory. This isn't usually enough to do much.

You can view how much memory is available when a custom amount may have been set as a default by running:

```
minikube config get memory
```

It is strongly recommended you configure Minikube to use 4Gi or more. This must be specified when the cluster is first created. This can be done by using the ``--memory`` option to ``minikube start``, or by specifying a default memory value beforehand using ``minikube config set memory``.

In addition to increasing the memory available, you may also want to look at increasing the disk size as fat container images can chew up disk space within the cluster pretty quickly.

When deploying workshops via the training portal, you can limit how much memory is being used by paying attention to the ``capacity``, ``initial`` and ``reserved`` properties. Certain configurations you find may pre create multiple workshop instances up front, or keep a new workshop instance in reserve ready for the next user. Because of the limited resources available to Minikube, it is recommend to only deploy one workshop at a time, and ensure a maximum of one is ever allowed to run at the same time.

A ``TrainingPortal`` configuration that does this is:

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: TrainingPortal
metadata:
  name: lab-markdown-sample
spec:
  workshops:
  - name: lab-markdown-sample
    capacity: 1
```

That is, ensure the ``initial`` and ``reserved`` properties are not set.

In this configuration, a single workshop instance will still be created up front. If you want to ensure the workshop instance is only created when required, and that it is shutdown automatically after a specified duration, or the session becomes inactive, use:

```yaml
apiVersion: training.eduk8s.io/v1alpha1
kind: TrainingPortal
metadata:
  name: lab-markdown-sample
spec:
  workshops:
  - name: lab-markdown-sample
    capacity: 1
    reserved: 0
    duration: 60m
    orphaned: 5m
```

With this configuration the workshop session will only be created on demand, and will be deleted automatically after 60 minutes if not shutdown before that. If you close the browser accessing the workshop without shutting it down, it will be shutdown and deleted after 5 minutes.

Storage provisioner bug
-----------------------

Version 1.12.3 of Minikube introduced a [bug](https://github.com/kubernetes/minikube/issues/8987) in the storage provisioner which causes potential corruption of data in persistent volumes where the same persistent volume claim name is used in two different namespaces. This will affect eduk8s where you deploy multiple training portals at the same time, where you run multiple workshops at the same time which have docker or image registry support enabled, or where the workshop session itself is backed by persistent storage and multiple sessions are run at the same time.

This issue is supposed to be fixed in Minikube version 1.13.0, however you can still encounter issues where deleting a training portal instance and then recreating it immediately with the same name. This is because reclaiming of the persistent volume by the Minikube storage provisioner can be slow and the new instance can grab the same original directory on disk with old data in it. As a result, always ensure you leave a bit of time between deleting a training portal instance and recreating it with the same name to allow the storage provisioner to delete the old persistent volume.
