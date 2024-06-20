(infrastructure-providers)=
Infrastructure Providers
========================

The Educates installation package provides pre-canned configurations for a number of infrastructure providers. These, as well as custom configurations for some other platforms are described below.

Installation to Amazon EKS
--------------------------

Installation is supported to [Amazon Elastic Kubernetes Service](https://aws.amazon.com/eks/). This is indicated by setting `provider` to `eks`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

Additional components can be installed upon specifying appropriate AWS credentials and service configuration.

...

Installation to Google GKE
--------------------------

Installation is supported to [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine). This is indicated by setting `provider` to `gke`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

Additional components can be installed upon specifying appropriate GCP credentials and service configuration.

...

Installation to local Kind
--------------------------

Installation is supported to a local Kubernetes cluster created using [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker). This is indicated by setting `provider` to `kind`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

For this case it is required that the Kind cluster be configured to [map ports 80/443](https://kind.sigs.k8s.io/docs/user/ingress/) such that the Kubernetes ingress controller is accessible via the host.

Installation to OpenShift
-------------------------

We are not currently providing a pre-canned configuration for installing Educates in OpenShift. We are working on including configuration for OpenShift, but believe the following configuration should work in the interim.

```yaml
# Specify the infrastructure provider hosting the Kubernetes cluster.
# We are using "custom" and providing the configuration ourselves.

clusterInfrastructure:
  provider: custom

# Specify the ingress domain to be used to access the workshops hosted by
# the Educates installation.

clusterIngress:
  domain: educates-local-dev.test

# Specify component packages to be installed for this configuration.

clusterPackages:
  # Disable installation of Contour as using OpenShift standard ingress
  # controller.

  contour:
    enabled: false

  # Enable installation of Kyverno for workshop security policy enforcement.

  kyverno:
    enabled: true

  # Ensure that Educates training platform is installed.

  educates:
    enabled: true

# Configure cluster security policy enforcement to be done using OpenShift
# security context constraints.

clusterSecurity:
  policyEngine: security-context-constraints

# Configure workshop security policy enforcement to be done using Kyverno.

workshopSecurity:
  rulesEngine: kyverno
```

The standard OpenShift ingress controller will be used.

Installation to a vCluster
--------------------------

Installation is supported to a Kubernetes virtual cluster using the [vCluster](https://www.vcluster.com/) software from [Loft Labs](https://loft.sh/). This is indicated by setting `provider` to `vcluster`.

The components which will be installed are the Educates training platform and Kyverno for cluster and workshop security policy enforcement.

For this case Kubernetes ingresses must still work within the virtual cluster. This means you need to have done one of the following:

* Pre-configure the virtual cluster to synchronize ingress resources from the virtual cluster to the underlying host Kubernetes cluster, so that ingresses created in the virtual cluster are handled by the ingress controller running in the underlying host Kubernetes cluster.
* Install a separate ingress controller into the virtual cluster with its own external ingress router for incoming traffic, or have the ingress controller of the underlying host Kubernetes cluster proxy to the ingress router of the virtual cluster for a suitable wildcard ingress domain.

Virtual clusters created by Educates itself as part of a workshop session satisfy this requirement for working ingresses, and as such it is possible to install Educates inside of Educates for the purposes of creating workshops to train users on Educates. In this scenario though, since security policies would be enforced by the underlying Educates installation, to reduce the amount of resources required and speed up installation of Educates inside of the virtual cluster, installation of Kyverno and enforcement of security policies can be disabled.

```yaml
# Specify the infrastructure provider hosting the Kubernetes cluster.

clusterInfrastructure:
  provider: vcluster

# Specify the ingress domain to be used to access the workshops hosted by
# the Educates installation.

clusterIngress:
  domain: educates-local-dev.test

# Disable the cluster and security policy engines, and skip installing
# Kyverno, as policies are enforced by the Educates installation running
# this workshop session.

clusterPackages:
  kyverno:
    enabled: false

clusterSecurity:
  policyEngine: none

workshopSecurity:
  rulesEngine: none
```
