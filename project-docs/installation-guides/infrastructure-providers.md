(infrastructure-providers)=
Infrastructure Providers
========================

The Educates installation package provides pre-canned configurations for a number of infrastructure providers. These, as well as custom configurations for some other platforms are described below.

Installation to Amazon EKS
--------------------------

Installation is supported on [Amazon Elastic Kubernetes Service](https://aws.amazon.com/eks/). This is indicated by setting `provider` to `eks`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

Additional components will be installed. These are:

* [external-dns](https://github.com/kubernetes-sigs/external-dns) - to configure a wildcard entry in your domain's desired `HostedZone`.
* [cert-manager](https://cert-manager.io/) - for certificate management integration with [Let's Encrypt](https://letsencrypt.org).
* certs - creates an ACME wildcard domain `ClusterIssuer` for `cert-manager`.

This installer package relies on having an EKS IAM Role for Service Account (IRSA) so you will need to create two IAM roles for both [external-dns](https://github.com/kubernetes-sigs/external-dns/blob/master/docs/tutorials/aws.md#iam-roles-for-service-accounts) and [cert-manager](https://cert-manager.io/docs/configuration/acme/dns01/route53/#eks-iam-role-for-service-accounts-irsa) services. The details of the roles need to be specified in the `aws.irsaRoles` section of the configuration, with a format `arn:aws:iam::<ACCOUNT_ID>:role/<ROLE_NAME>`.

Additionally, you need to specify the AWS region where your cluster is running, and if the domain you're using is not a real `HostedZone` in AWS, you may need to specify `aws.route53.hostedZone` with the actual domain. 

This is a sample snippet that will get Educates installed on an existing EKS cluster.

```yaml
clusterInfrastructure:
  provider: "eks"
  aws:
    region: "eu-west-1"
    route53:
      hostedZone: "example.com"
    irsaRoles:
      external-dns: "arn:aws:iam::123456789012:role/external-dns"
      cert-manager: "arn:aws:iam::123456789012:role/cert-manager"
clusterIngress:
  domain: "educates.example.com"
```

Installation to Google GKE
--------------------------

Installation is supported on [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine). This is indicated by setting `provider` to `gke`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

Additional components will be installed. These are:

* [external-dns](https://github.com/kubernetes-sigs/external-dns) - to configure a wildcard entry in your domain's desired DNS Zone in Google CloudDNS.
* [cert-manager](https://cert-manager.io/) - for certificate management integration with [Let's Encrypt](https://letsencrypt.org).
* certs - creates an ACME wildcard domain `ClusterIssuer` for `cert-manager`.

This installer package relies on having an [GKE Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) so you will need to create two IAM roles for both [external-dns](https://github.com/kubernetes-sigs/external-dns/blob/master/docs/tutorials/nginx-ingress.md#gke-with-workload-identity) and [cert-manager](https://cert-manager.io/docs/configuration/acme/dns01/google/#gke-workload-identity) services. The details of the roles need to be specified in the `gcp.workloadIdentity` section of the configuration, with a format `<ROLE_NAME>@<PROJECT_ID>.iam.gserviceaccount.com`

Additionally, you need to specify the Google project Id for your GKE cluster, and if the domain you're using is not a real DNS Zone in Google CloudDNS, you may need to specify the `gcp.cloudDNS.zone` with the actual domain. 

This is a sample snippet that will get Educates installed on an existing GKE cluster.

```
clusterInfrastructure:
  provider: "gke"
  gcp:
    project: "my-project"
    cloudDNS:
      zone: "example.com"
    workloadIdentity:
      external-dns: "external-dns@my-project.iam.gserviceaccount.com"
      cert-manager: "cert-manager@my-project.iam.gserviceaccount.com"
clusterIngress:
  domain: "educates.example.com"
```

Installation to local Kind
--------------------------

Installation is supported on a local Kubernetes cluster created using [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker). This is indicated by setting `provider` to `kind`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

For this case it is required that the Kind cluster be configured to [map ports 80/443](https://kind.sigs.k8s.io/docs/user/ingress/) such that the Kubernetes ingress controller is accessible via the host. The wildcard ingress domain must map to the host IP.

Note that if using the `educates create-cluster` command the Kind cluster will be created for you.

Installation to Minikube
------------------------

Installation is supported on a local Kubernetes cluster created using [Minikube](https://minikube.sigs.k8s.io). This is indicated by setting `provider` to `minikube`.

The components which will be installed are the Educates training platform, Contour as the ingress controller, and Kyverno for cluster and workshop security policy enforcement.

If using the `docker` driver for Minikube, you will need to use the `minikube tunnel` command to expose the ingress controller and the wildcard ingress domain must map to the host IP.

If using a driver for Minikube which exposes the cluster on it's own IP address, the wildcard ingress domain must map to the IP of the Minikube cluster.

If you do not want to use Contour as the ingress controller, but use the Nginx ingress controller directly supported by Minikube, you can instead set `provider` to `generic`, or alternatively still use `minikube`, but disable installation of Contour.

Installation to OpenShift
-------------------------

Installation is supported on a local Kubernetes cluster created using [OpenShift](https://docs.openshift.com). This is indicated by setting `provider` to `openshift`.

The components which will be installed are the Educates training platform, and Kyverno for workshop security policy enforcement.

OpenShift security context constraints (SCC) will be used for cluster security policies. For ingress, the native OpenShift ingress controller will be used.

Installation to a vCluster
--------------------------

Installation is supported on a Kubernetes virtual cluster using the [vCluster](https://www.vcluster.com/) software from [Loft Labs](https://loft.sh/). This is indicated by setting `provider` to `vcluster`.

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
