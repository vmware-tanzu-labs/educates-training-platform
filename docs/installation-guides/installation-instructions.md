Installation Instructions
=========================

The installation instructions given here are only needed if you are installing into a dedicated Kubernetes cluster and not using the [local Educates environment](quick-start-guide). Ensure you have read the general documentation about [cluster requirements](cluster-requirements) before proceeding with trying to install Educates.

Educates provides a package for installing an ingress controller and other operators it requires, such as Kyverno, so you do not need to have installed these first. Further information on installing these is given below.

Carvel command line tools
-------------------------

These instructions require that you have the Carvel command tools installed and available on the machine from which you are installing Educates. For installing these see:

* [https://carvel.dev/](https://carvel.dev/)

The tools can be installed using a shell script provided by the Carvel project, or using Homebrew on macOS and Linux.

Ensure you are using an up to date version of the tools, and that if you used Homebrew to perform the install, and that was first done a long time ago, that the more recently added ``kctrl`` command line tool was included.

Installing kapp-controller
--------------------------

The standard method for installing Educates relies on the Carvel packaging system and requires that [kapp-controller](https://carvel.dev/kapp-controller/) from Carvel be installed into the Kubernetes cluster.

If you are using a Kubernetes cluster created using Tanzu Community Edition (TCE), Tanzu Kubernetes Grid (TKG) or Tanzu Mission Control (TMC), it will come preinstalled with ``kapp-controller`` and you do not need to install ``kapp-controller`` yourself.

If you do need to install ``kapp-controller``, further information can be found at:

* [https://carvel.dev/kapp-controller/docs/develop/install/](https://carvel.dev/kapp-controller/docs/develop/install/)

In most circumstances all you should need to do is run:

```bash
kapp deploy -a kc -f https://github.com/vmware-tanzu/carvel-kapp-controller/releases/latest/download/release.yml
```

Loading package definitions
---------------------------

The Carvel packaging ecosystem supports the concept of hosted package repositories. At this time there is no package repository for Educates so you will need to manually load the package definitions into your Kubernetes cluster.

Package definitions for Educates can be obtained from the releases page of the Educates GitHub repository:

* [https://github.com/vmware-tanzu-labs/educates-training-platform/releases](https://github.com/vmware-tanzu-labs/educates-training-platform/releases)

For the release version you wish to use, download the two files attached as assets of the form:

* ``educates-cluster-essentials-X.Y.Z.yaml``
* ``educates-training-platform-X.Y.Z.yaml``

From your local machine, load these into the Kubernetes cluster by running:

```bash
kubectl apply -n kapp-controller-packaging-global -f educates-cluster-essentials-X.Y.Z.yaml
kubectl apply -n kapp-controller-packaging-global -f educates-training-platform-X.Y.Z.yaml
```

You can verify they are loaded by running:

```bash
kubectl get packages -n kapp-controller-packaging-global
```

Installing cluster essentials
-----------------------------

Educates requires that an ingress controller be installed into the Kubernetes cluster. The recommended ingress controller is [Contour](https://projectcontour.io/).

If an ingress controller has not already been installed, you can install the ``educates-cluster-essentials`` package to install Contour.

The ``educates-cluster-essenstials`` package will also install Kyverno. Kyverno is used for security policy enforcement of workshop sessions.

To configure this package create a values file called ``educates-cluster-essenstials-values.yaml`` containing:

```yaml
clusterPackages:
  contour:
    enabled: true
    settings: {}
  kyverno:
    enabled: true
    settings: {}

clusterInfrastructure:
  provider: ""

clusterSecurity:
  policyEngine: "none"
```

This represents the default configuration.

If a suitable ingress controller is already installed set ``clusterPackages.contour.enabled`` to ``false``.

If you are installing on OpenShift, ``clusterPackages.contour.enabled`` must be set to ``false`` as OpenShift already provides an ingress controller in its default installation.

If Kyverno is already installed set ``clusterPackages.kyverno.enabled`` to ``false``.

If neither is required you can skip installing the package completely.

If you are installing to a local Kubernetes cluster created using ``Kind``, set ``clusterInfrastructure.provider`` to ``kind``. The effect of setting this to ``kind`` will be to configure Contour to only create a ``ClusterIP`` service for Envoy and use host ports, and not a load balancer service. It is important that the Kubernetes cluster created using ``Kind`` exports the ingress controller host ports to the underlying host system in this case.

At this time there is no need to set ``clusterInfrastructure.provider`` for any other infrastructure provider, and in those cases Contour will use a ``LoadBalancer`` service for Envoy.

If you need to override any other configuration for Contour, you can add values to ``clusterPackages.contour.settings``. These should correspond to the values accepted for the Contour Carvel package provided by TCE.

* [https://github.com/vmware-tanzu/community-edition/tree/main/addons/packages/contour](https://github.com/vmware-tanzu/community-edition/tree/main/addons/packages/contour)

Next you must override the value of ``clusterSecurity.policyEngine``. The value depends on how your Kubernetes cluster is configured.

If you are installing to OpenShift, ``clusterSecurity.policyEngine`` must be set to ``security-context-constraints``.

If you are installing to a Kubernetes cluster which has pod security policies enabled, and it associates a default pod security policy with all authenticated users, ``clusterSecurity.policyEngine`` must be set to ``pod-security-policies``.

For all other cases you should override ``clusterSecurity.policyEngine`` and set it to ``kyverno``.

If you leave ``clusterSecurity.policyEngine`` set as ``none``, then no security policy enforcement will be done, in which case workshop users would not be restricted from running containers with elevated privileges. Using ``none`` is okay for testing on your own local system, but should never be done where untrusted users would be doing workshops. If you do use ``none`` and develop your own workshops, you may also find those workshops will then not work on an Educates instance which does security policy enforcement. It is thus recommended to always at least set this to ``kyverno`` if not restricted otherwise by how the Kubernetes cluster is configured.

Note that the same setting used here for ``clusterSecurity.policyEngine`` will also need to be used later when installing the Educates training platform package.

To install the ``educates-cluster-essenstials`` package now run:

```bash
kctrl package install --package-install educates-cluster-essentials --package cluster-essentials.educates.dev --version "X.Y.Z" --values-file educates-cluster-essenstials-values.yaml
```

Ensure you subsitute ``X.Y.Z`` with the actual version corresponding to the package definition which was loaded.
