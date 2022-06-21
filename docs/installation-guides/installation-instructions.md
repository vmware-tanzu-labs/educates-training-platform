(installation-instructions)=
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

(installing-cluster-essentials)=
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
  policyEngine: "kyverno"
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

You can if necessary set ``clusterSecurity.policyEngine`` to ``none``, but no security policy enforcement will be done, in which case workshop users would not be restricted from running containers with elevated privileges. Using ``none`` is okay for testing on your own local system, but should never be done where untrusted users would be doing workshops. If you do use ``none`` and develop your own workshops, you may also find those workshops will then not work on an Educates instance which does security policy enforcement. It is thus recommended to always at least set this to ``kyverno`` if not restricted otherwise by how the Kubernetes cluster is configured.

Note that the same setting used here for ``clusterSecurity.policyEngine`` will also need to be used later when installing the Educates training platform package.

To install the ``educates-cluster-essenstials`` package now run:

```bash
kctrl package install -n default --package-install educates-cluster-essentials --package cluster-essentials.educates.dev --version "X.Y.Z" --values-file educates-cluster-essenstials-values.yaml
```

Ensure you subsitute ``X.Y.Z`` with the actual version corresponding to the package definition which was loaded.

Cluster ingress domain
----------------------

For Educates to work it needs to be configured with an ingress domain.

If you want to configure Educates to use secure ingress, you need to have a wildcard TLS certificate for that ingress domain. If you do not have a wildcard TLS certificate for the ingress domain, then some features of workshops (such as per session image registries) will not work.

The preferred scenario is that you bring your own custom domain name and matching wildcard TLS certificate for that domain.

The first required step in using your own custom domain is to configure your DNS servers with a ``CNAME`` or equivalent entry to map all host name lookups under the domain (e.g., ``*.example.com``) to the IP address or host name of the inbound ingress router for the Kubernetes cluster. How you calculate the IP address or host name of the inbound ingress router will depend on what infrastructure is being used to host the Kubernetes cluster and how the ingress controller was installed.

In the simplest case, using Contour installed with the ``educates-cluster-essenstials`` package where a ``LoadBalancer`` service type for Envoy is being used, you may be able to determine the IP address or host name of the inbound ingress router by running:

```bash
kubectl get service/envoy -n projectcontour
```

If you have a matching wildcard TLS certificate for the ingress domain, you now need to create a Kubernetes secret for the certificate and load it into the Kubernetes cluster.

If you had used ``certbot`` to generate the certificate from LetsEncrypt using a DNS challenge, you should be able to create the secret resource file using a command similar to:

```bash
kubectl create secret tls example.com-tls --cert=$HOME/.letsencrypt/config/live/example.com/fullchain.pem --key=$HOME/.letsencrypt/config/live/example.com/privkey.pem --dry-run=client -o yaml > example.com-tls.yaml
```

Replace ``example.com`` with the name of your custom domain name.

Load the secret into the Kubernetes cluster using:

```bash
kubectl apply -n default -f example.com-tls.yaml
```

In this case we created the secret in the ``default`` namespace. You can use a different namespace if desired as the namespace will need to be listed explicitly in the configuration for Educates in a subsequent step.

If you do not have your own custom domain name, it is possible to use a ``nip.io`` address mapped to the IP address of the inbound ingress router host, however, because it will not be possible to obtain a TLS certificate for the domain, you will not be able to use secure ingress.

(create-the-configuration)=
Create the configuration
------------------------

With the pre-requisites now installed in the Kubernetes cluster, installation of the Educates training platform can be done using the ``educates-training-platform`` package.

To configure this package create a values file called ``educates-training-platform-values.yaml`` containing:

```yaml
clusterIngress:
  domain: "example.com"
  tlsCertificateRef:
    namespace: "default"
    name: "example.com-tls"

clusterSecurity:
  policyEngine: "kyverno"

workshopSecurity:
  rulesEngine: "kyverno"
```

This is the most minimal configuration needed to install the Educates training platform.

Set ``clusterSecurity.policyEngine`` to the same value you used when installing the ``educates-cluster-essentials`` package.

That is, if you are installing to OpenShift, ``clusterSecurity.policyEngine`` must be set to ``security-context-constraints``.

If you are installing to a Kubernetes cluster which has pod security policies enabled, and it associates a default pod security policy with all authenticated users, ``clusterSecurity.policyEngine`` must be set to ``pod-security-policies``.

For all other cases you should override ``clusterSecurity.policyEngine`` and set it to ``kyverno``.

The value of ``workshopSecurity.rulesEngine`` should also be set to ``kyverno``. If can be set to ``none``, and this is okay for testing on your own local system, but should never be done where untrusted users would be doing workshops.

For ingresses, set ``clusterIngress.domain`` to your custom domain name, or appropriate ``nip.io`` domain.

If you have a wildcard TLS certificate, update ``clusterSecurity.tlsCertificateRef.name``, setting it to the name of the Kubernetes secret you created containing it. Change ``clusterSecurity.tlsCertificateRef.name`` if you created the secret in a namespace other than ``default``.

If you do not have a wildcard TLS for the domain name you are using, delete the ``tlsCertificateRef`` section, including everything under it. If you comment out the section instead, you must use the ``#!`` comment prefix.

There are a range of other settings that can optionally be set. For more details on these settings and whether you may need to use them see the documentation on {any}`configuration settings <configuration-settings>`.

Installing training platform
----------------------------

To install the ``educates-training-platform`` package now run:

```bash
kctrl package install -n default --package-install educates-training-platform --package training-platform.educates.dev --version "X.Y.Z" --values-file educates-training-platform-values.yaml
```

Ensure you subsitute ``X.Y.Z`` with the actual version corresponding to the package definition which was loaded.

Deleting the installation
-------------------------

It is recommended to remove any workshop environments before deleting Educates from the Kubernetes cluster. This will ensure that everything can be cleaned up properly.

To delete all current running workshop environments run:

```bash
kubectl delete workshops,trainingportals,workshoprequests,workshopsessions,workshopenvironments --all --cascade=foreground
```

The ``--cascade=foreground`` command ensures that the command only returns once all workshop environments have been deleted. This is necessary as otherwise deletion will occur in the background.

To make sure everything is deleted, run:

```bash
kubectl get workshops,trainingportals,workshoprequests,workshopsessions,workshopenvironments --all-namespaces
```

There should be nothing remaining.

The Educates training platform can then be deleted by running:

```bash
kctrl package installed delete -n default --package-install educates-training-platform
```

and confirming that you want to delete it.

Once deletion has finished you can safely re-install the Educates training platform.

If you instead wanted to clean up everything, you can also delete the pre-requisites installed above using:

```bash
kctrl package installed delete -n default --package-install educates-cluster-essentials
```

The package definitions can then be deleted using:

```bash
kubectl apply -n kapp-controller-packaging-global package/educates-cluster-essentials-X.Y.Z
kubectl apply -n kapp-controller-packaging-global package/educates-training-platform-X.Y.Z
```

Ensure you subsitute ``X.Y.Z`` with the actual version corresponding to the package definition which was loaded.

Finally, delete the Kubernetes secret you created for your wildcard TLS certificate if desired.

Note that if the ``educates-cluster-essentials`` package was used to install Contour and you were intending to use the Kubernetes cluster for some other purpose, you would need to re-install an ingress controller using some other method.
