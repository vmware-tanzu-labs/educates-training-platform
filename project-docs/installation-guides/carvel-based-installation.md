Carvel Based Installation
=========================

Of the two methods available for installing Educates into an existing Kubernetes cluster, the instructions below pertain to installing Educates via the Carvel `kapp-controller` operator pre-installed into a Kubernetes cluster. The instructions assume you have already prepared a suitable configuration file.

Carvel command line tools
-------------------------

The Carvel project provides a set of command line tools you can run locally, as well as a number of operators for installation in to Kubernetes clusters for package and secrets management.

In order to install Educates, you do not actually need to have the Carvel tools installed locally, but if you are interested in what they can do for you, see the [Carvel](https://carvel.dev/) project web site.

Installing kapp-controller
--------------------------

To install Educates into a Kubernetes cluster using the Carvel packaging system requires that [kapp-controller](https://carvel.dev/kapp-controller/) from Carvel be installed into the Kubernetes cluster.

If you are using a Kubernetes cluster created using Tanzu Kubernetes Grid (TKG) or Tanzu Mission Control (TMC), it will come preinstalled with ``kapp-controller`` and you do not need to install ``kapp-controller`` yourself.

If you do need to install ``kapp-controller``, further information can be found at:

* [https://carvel.dev/kapp-controller/docs/develop/install/](https://carvel.dev/kapp-controller/docs/develop/install/)

In most circumstances all you should need to do is run:

```bash
kubectl deploy -f https://github.com/vmware-tanzu/carvel-kapp-controller/releases/latest/download/release.yml
```

Installer service account
-------------------------

...
