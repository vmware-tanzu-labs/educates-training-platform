Quick Start Guide
=================

The quickest way to install and start experimenting with Educates is to install it on your local machine using a Kubernetes cluster created using Kind. To make this process easier, Educates provides a set of scripts you can use to create the cluster and deploy Educates.

A detailed description on how to install Educates into any Kubernetes cluster is included later in the documentation.

Host system requirements
------------------------

To deploy Educates on your local machine using the available scripts the following are required:

* You need to be running macOS or Linux. If using Windows you will need WSL (Windows subsystem for Linux). The scripts have been tested on macOS.

* You need to have a working `docker` environment. The scripts have been tested with Docker Desktop.

* You need to have sufficient memory and disk resources allocated to the `docker` environment to run Kubernetes, Educates etc.

* You cannot be running an existing Kubernetes cluster created using Kind.

* You cannot be using port 80 (HTTP) and 443 (HTTPS) on the local machine as these will be required by the Kubernetes ingress controller.

* You need to have port 53 (DNS) available on the local machine when using macOS if you want to enable a local DNS resolver.

* You need to have port 5001 available on the local machine as this will be used for a local image registry.

* You need to have the [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) command line client installed on your local machine.

* You need to have the [Carvel](https://carvel.dev/) toolset installed on your local machine.

Downloading the scripts
-----------------------

If you have access to the GitHub `vmware-tanzu-labs` organization, to download the scripts for creating a local Kubernetes cluster you can checkout a copy of the Git repository hosting the scripts by running:

```
git clone git@github.com:vmware-tanzu-labs/educates-local-dev.git
```

If you not have access to the GitHub `vmware-tanzu-labs` organization, instead run:

```
imgpkg pull -i ghcr.io/vmware-tanzu-labs/educates-local-dev:latest -o educates-local-dev
```

The `imgpkg` command is from the [Carvel](https://carvel.dev/) toolset.

Default ingress domain
----------------------

Educates requires a valid fully qualified domain name (FQDN) to use with Kubernetes ingresses which it creates.

By default, the scripts will automatically use a `nip.io` address which consists of the IP address of your local machine as the ingress domain. For example `192.168.1.1.nip.io`.

If a `nip.io` address is relied upon, some features of Educates will not be able to be used. This is because those features require that you also have access to a wildcard TLS certificate for the ingress domain. Since you don't control the `nip.io` domain, there is no way for you to generate the required TLS certificate.

For the initial deployment we will rely on a `nip.io` address. How to use an alternate ingress domain and a TLS certificate will be covered later.

Local Kubernetes cluster
------------------------

To create the local Kubernetes cluster using Kind, run the script:

```
educates-local-dev/create-cluster.sh
```

This script will preform the following steps:

* Deploy a container image registry in the `docker` environment, running on port 5001.

* Create the Kubernetes cluster using Kind.

* Configure the Kubernetes cluster to trust the container image registry.

* Enable pod security policies in the Kubernetes cluster.

* Install Contour into the Kubernetes cluster and expose it via ports 80/443 on the local machine.

* Deploy Educates to the Kubernetes cluster.

Once the Kubernetes cluster has been created, you should be able to access it immediately using `kubectl` as the configuration will be added to your local Kube configuration. The name of the Kube config context for the cluster is `kind-educates`.

Deploying a workshop
--------------------

The Educates documentation is intended primarily for people who need to create workshop content. Before we get to showing how you can create your own workshop, let's start by deploying an existing workshop. In this case we will use an existing workshop which teaches about the fundamentals of using a Kubernetes cluster to deploy an application.

To deploy this workshop first run:

```
kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/1.0/workshop.yaml
```

This will load a `Workshop` resource definition into the Kubernetes cluster which describes the workshop, including where the workshop content is located and any special configuration required to deploy it.

The output from running this command should in this case be:

```
workshop.training.eduk8s.io/lab-k8s-fundamentals created
```

To have an environment setup to run this workshop, and be able to access it, you next need to create an instance of a training portal. This will provide the web interface for accessing the workshop, as well as manage the workshop environment.

To deploy a training portal instance configured to use this workshop run:

```
kubectl apply -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/download/1.0/training-portal.yaml
```

This will load a `TrainingPortal` resource definition, which will trigger Educates to create the training portal and workshop environment.

The output from running this command should in this case be:

```
trainingportal.training.eduk8s.io/lab-k8s-fundamentals created
```

Accessing the workshop
----------------------

To access the workshop you just deployed, run:

```
kubectl get trainingportals
```

This should output:

```
NAME                  URL                                                ADMINUSERNAME  ADMINPASSWORD  STATUS
lab-k8s-fundamentals  http://lab-k8s-fundamentals-ui.192.168.1.1.nip.io  educates       my-pasword     Running
```

The domain name in the URL will likely differ, as it will use the IP address of your local machine.

Go to this URL in your web browser. From the training portal dashboard you should be able to start a workshop session.

Note that the first time you run a workshop it may be slow to startup as the container image for the workshop environment will need to be pulled down to the local Kubernetes cluster. So be a bit patient if you have a slow internet connection.

When you have completed the workshop and you exit it, the workshop session will be shutdown and you will be returned to the training portal dashboard.

Deleting the workshop
---------------------

When you no longer require this workshop and wish to delete the workshop environment and training portal, run:

```
kubectl delete workshop,trainingportal lab-k8s-fundamentals
```

The output should be:

```
workshop.training.eduk8s.io "lab-k8s-fundamentals" deleted
trainingportal.training.eduk8s.io "lab-k8s-fundamentals" deleted
```
