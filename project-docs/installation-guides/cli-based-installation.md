CLI Based Installation
======================

Of the two methods available for installing Educates into an existing Kubernetes cluster, the instructions below pertain to installing using the Educates CLI. The instructions assume you have already prepared a suitable configuration file.

Deploying the platform
----------------------

Once you have created a suitable configuration file, you can install Educates into an existing Kubernetes cluster using the Educates CLI, by running:

```shell
educates deploy-platform --config config.yaml
```

The `--config` option should supply the path to the configuration file you created.

You must have set `clusterInfrastructure.provider` in the configuration file.

The installation process will install Educates, as well as other services and Kubernetes operators required by Educates, or which are beneficial when working with the specified infrastructure provider.

If needing to debug the installation process, you can supply the `--verbose` option.

```shell
educates deploy-platform --config config.yaml --verbose
```

Kubeconfig and context
----------------------

By default the Educates CLI will use the Kubernetes configuration found in the standard `kubeconfig` file, usually `$HOME/.kube/config`.

If you want to use an alternate `kubeconfig` file, use the `--kubeconfig` option.

```shell
educates deploy-platform --config config.yaml --kubeconfig kubeconfig.yaml
```

Whether the default `kubeconfig` or one supplied using the `--kubeconfig` option, the current context specified by the configuration will be used.

If you want to specify an alternate context be used, use the `--context` option.

```shell
educates deploy-platform --config config.yaml --context educates-cluster
```

Updating configuration
----------------------

After having performed an installation, if you needed to amend the configuration, in many cases it is possible to update the configuration for the installation in place, without needing to delete the installation and reinstall it.

To update the configuration for the already deployed installation, make the required changes to your configuration file. You can then run the same command as you used originally to install it. For example:

```shell
educates deploy-platform --config config.yaml
```

Note that such configuration changes will not necessarily affect training portals or workshop environments which have already been created, and will only affect training portals created after that point.

Deleting the installation
-------------------------

To delete Educates and any other services or Kubernetes operators which were installed, you can run:

```shell
educates delete-platform
```
