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
kubectl apply -f https://github.com/vmware-tanzu/carvel-kapp-controller/releases/latest/download/release.yml
```

Installer service account
-------------------------

When using `kapp-controller` to install a package, it is necessary to provide a service account in the Kubernetes cluster which has the required role access to be able to create all the resources for a package. This service account must be granted any required roles which the deployed application needs at runtime.

Because the Educates training platform may need to create instances of any available Kubernetes resource type when deploying specific workshops, it needs to have full `cluster-admin` role access.

To create the required service account and role bindings a YAML resources file is provided with each Educates release. To apply this for the latest version of Educates to the cluster, run the command:

```bash
kubectl apply -f https://github.com/vmware-tanzu-labs/educates-training-platform/releases/latest/download/educates-installer-app-rbac.yaml
```

Alternatively, checkout the [Educates releases](https://github.com/vmware-tanzu-labs/educates-training-platform/releases) and use the `educates-installer-app-rbac.yaml` file from the specific version of Educates you want to install.

Note that a namespace called `educates-installer` will be created to hold the service account.

Applying the package values
---------------------------

The next required step is to create a secret in the Kubernetes cluster which holds the configuration you want to use for deploying Educates.

Presuming your configuration is in the `config.yaml` file, run:

```bash
kubectl create secret generic educates-installer -n educates-installer --from-file config.yaml --save-config
```

The secret should be created in the `educates-installer` namespace.

Installing Educates package
---------------------------

You are now ready to install Educates and any required services as dictated by the configuration you supplied.

For the latest version of Educates, run the following command:

```bash
kubectl apply -f https://github.com/vmware-tanzu-labs/educates-training-platform/releases/latest/download/educates-installer-app.yaml
```

Alternatively, checkout the [Educates releases](https://github.com/vmware-tanzu-labs/educates-training-platform/releases) and use the `educates-installer-app.yaml` file from the specific version of Educates you want to install.

The same `educates-installer` namespace referenced in prior steps will be used.

Updating package configuration
------------------------------

To update the configuration for the installed package, update the values in the `educates-installer` secret.

```bash
kubectl create secret generic educates-installer -n educates-installer --from-file config.yaml --dry-run=client -o yaml | kubectl apply -f -
```

The next time that `kapp-controller` performs a reconcilliation for the package, the new configuration will be applied.

If you need to manually force reconcilliation you can run:

```bash
kctrl app kick -a installer.educates.dev -n educates-installer -y
```

The `kctrl` command is from the Carvel package toolset.

Note that such configuration changes will not necessarily affect training portals or workshop environments which have already been created, and will only affect training portals created after that point.

Deleting the installed package
------------------------------

To delete everything installed with the Educates package, run:

```bash
kubectl delete -n educates-installer app/installer.educates.dev
```

This will leave the `educates-installer` namespace, the service account which was created, as well as the secret holding the Educates configuration.

To manually clean these up run:

```bash
kubectl delete namespace/educates-installer
kubectl delete clusterrolebinding/educates-installer
```
