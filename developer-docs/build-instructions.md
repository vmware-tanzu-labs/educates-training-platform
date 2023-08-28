Build Instructions
==================

If you are hoping to contribute to Educates, before you attempt to build a local version of Educates and start modifying any code, read our [contribution guidelines](../CONTRIBUTING.md) and reach out to us to discuss any changes you are considering.

Local Kubernetes environment
----------------------------

To do development on the core Educates platform you will need access to a Kubernetes cluster. For this we recommend you use a local Kubernetes cluster created using [Kind](https://kind.sigs.k8s.io/). Rather than you create this Kind cluster yourself, you can create it using the `educates` CLI. This will ensure that the Kind cluster is setup properly for how the Educates code is structured for doing local development.

When creating a local Kubernetes cluster with Educates the `educates create-cluster` command is used. For the case of wanting to do local development on Educates itself, you need to disable installation of the services required by Educates, and the core Educates platform. This is done using the command:

```
educates create-cluster --with-services=false --with-platform=false
```

You can subsequently delete the local Kubernetes environment by running:

```
educates delete-cluster
```

Ensure you read the main Educates documentation quick start guide for any requirements around running the local Kubernetes cluster and Educates, deployed using the `educates` CLI.

Local docker image registry
---------------------------

When the local Kubernetes cluster is created using `educates create-cluster`, a local docker image registry will also be deployed to the local docker environment.

The docker image registry will be available at `localhost:5001` and will be used to hold container images built from the Educates source code. This image registry will also be used as the source of images when Educates is deployed to the local Kubernetes cluster.

If over time the amount of storage consumed by the local docker image registry increases to the point where overall available space within the local docker environment runs low, you can try to clean out unreferenced image layers by running:

```
docker image prune
```

If you need to delete the local docker image registry and redeloy it, you can run:

```
educates admin registry delete
```

to delete it, and:

```
educates admin registry deploy
```

to recreate it.

Note that this later command will create/update service resources in the Kubernetes cluster which are used to map and make available the local docker registry in the cluster. The original `educates create-cluster` command will also configure `containerd` within the Kubernetes cluster to trust the local docker image registry. It is thus important to use the `educates` CLI to deploy the local docker image registry rather than attempting to deploy a local docker image registry yourself.

Ingress router and other services
---------------------------------

Educates requires a functional ingress router to be deployed to the Kubernetes cluster. To make it easier to install this Educates provides the `educates-cluster-essentials`. This package includes the Contour ingress router as well as other services required by Educates.

If you are not working on code changes to the `educates-cluster-essentials` package itself, you can use the `educates` CLI to install a previously released version of the package by running:

```
educates admin services deploy
```

You could also have left out the `--with-services=false` option to `educates create-cluster` when creating the local Kubernetes cluster.

When this package is installed using the `educates` CLI, it is required that `kapp-controller` be installed into the Kubernetes cluster. This is something you do not need to do though as `kapp-controller` will be automatically installed by the `educates create-cluster` command.

Note that the version of the package which is installed will be that which corresponds to the version of the `educates` CLI being used. If you have compiled the `educates` CLI from local source code, then it will be tagged as being the `develop` version and the `develop` versions of the packages available on GitHub container registry may be out of date at any particular time. Thus if using locally compiled `educates` CLI, you should specify the version to be used.

```
educates admin services deploy --version X.Y.Z
```

Normally you would pick whatever is the latest Educates version.

If needing to delete all the services deployed using the `educates-cluster-essentials` package using the `educates` CLI you can run the command:

```
educates admin services delete
```

If you are going to be working on the `educates-cluster-essentials` package, you should instead install it from the local source code by running:

```
make deploy-cluster-essentials
```

To avoid some of the complexity of using `kapp-controller` this will use `kapp` rather than `kapp-controller`.

If needing to test that the `educates-cluster-essentials` package bundle for `kapp-controller` is itself correct, you should instead use the commands:

```
make push-cluster-essentials-bundle
make deploy-cluster-essentials-bundle
```

To delete all the services deployed using the `educates-cluster-essentials` package when using the `make` command, use:

```
make delete-cluster-essentials
```

or:

```
make delete-cluster-essentials-bundle
```

as appropriate.

Note that because the core Educates platform has dependencies on this package, if deleting this package you should first delete the core Educates platform, and reinstall it after this package has been reinstalled.

Installing the Educates platform
--------------------------------

If working on the `educates-cluster-essentials` package and installing it from local source code, and you need to install the core Educates platform on top, it is available as the `educates-training-platform` package.

To install this using a previously released version of the package you can run:

```
educates admin platform deploy
```

Note that the version of the package which is installed will be that which corresponds to the version of the `educates` CLI being used. If you have compiled the `educates` CLI from local source code, then it will be tagged as being the `develop` version and the `develop` versions of the packages available on GitHub container registry may be out of date at any particular time. Thus if using locally compiled `educates` CLI, you should specify the version to be used.

```
educates admin platform deploy --version X.Y.Z
```

Normally you would pick whatever is the latest Educates version.

If needing to delete all the services deployed using the `educates-training-platform` package using the `educates` CLI you can run the command:

```
educates admin platform delete
```

Building Educates platform images
---------------------------------

If you will be working on the core Educates platform, you will first need to build the container images for the `educates-training-platform` package. To do this you can run:

```
make push-core-images
```

This will trigger the building of the container images and push the resulting images to the local docker image registry.

Targets for make are also available for building and pushing to the local docker image registry individual container images.

```
make push-session-manager
make push-secrets-manager
make push-training-portal
...
```

See the [Makefile](../Makefile) for more details of the make targets that are available.

Once the container images have been built and pushed to the local docker image registry, you can then deploy the core Educates platform by running:

```
make deploy-training-platform
```

As with the `educates-cluster-essentials` package, to avoid some of the complexity of using `kapp-controller` this will use `kapp` rather than `kapp-controller`.

If needing to test that the `educates-training-platform` package bundle for `kapp-controller` is itself correct, you should instead use the commands:

```
make push-training-platform-bundle
make deploy-training-platform-bundle
```

To delete all the services deployed using the `educates-training-platform` package when using the `make` command, use:

```
make delete-training-platform
```

or:

```
make delete-training-platform-bundle
```

as appropriate.

Overriding default configuration
--------------------------------

When deploying the `educates-cluster-essentials` and `educates-training-platform` packages from local source code the builtin defaults for configuration will be used. If you need to override these you need to provide appropriate data values files in the `developer-testing` subdirectory.

* developer-testing/educates-cluster-essentials-values.yaml
* developer-testing/educates-training-platform-values.yaml

For specific details on what these need to provide see the main Educates documentation about configuration settings for Educates when deploying using the Carvel packages.

Building additional workshop images
-----------------------------------

When using `make push-core-images`, it will only build the main workshop base image. That is, it will not build workshop base images for Java and Python.

If you want to build all workshop base images you can instead run:

```
make push-all-images
```

Note that this will consume a lot more storage space in the local docker environment. In general you will probably want to configure the local docker environment with 100Gi or more of storage space to be used across local image caching, the local docker image registry and the Kubernetes cluster itself.

As well as the `push-all-images`, make targets are also supplied for building and pushing to the local docker image registry individual workshop base images.

```
make push-base-environment
make push-jdk8-environment
make push-jdk11-environment
make push-jdk17-environment
make push-conda-environment
```

See the [Makefile](../Makefile) for more details of the make targets that are available.

Building the Educates CLI program
---------------------------------

If needing to work on the `educates` CLI it can be built using the command:

```
make client-programs
```

You can then run the `educates` command from the `client-programs` subdirectory.

Note that when building the `educates` CLI from local source code, the embedded project version will be `develop`. If you are running it to test creation of an Educates cluster, or installing the cluster essentials or training platform packages, you will need to tell it what previously released versions of the package should be used. This can be done using the `--version` of sub commands where this is necessary.

Cleaning up available storage space
-----------------------------------

Running successive builds of the container images will incrementally result in more and more storage space being consumed as all layers of builds will be cached even if no longer being used.

Commands such as `docker image prune` can prune images from the local docker build cache, but will not reclaim storage for unused image layers in the local docker image registry.

To clean up available storage space across the local docker image build cache, the local docker image registry, and also any local file system space used to to local source code builds you can run:

```
make prune-all
```

Note that this will run `docker system prune` rather than `docker image prune`, which will also result in unused docker networks and volumes being cleaned up.

Also note that this doesn't reclaim space used by the image cache of `containerd` on the Kubernetes cluster nodes. If you are doing a lot of work on Educates, especially changes to the workshop base images and you deploy workshops using many successive versions of the images, eventually you can run out of storage space due to the `containerd` image cache. In this case there isn't really anything simple you can except for deleting the Kubernetes cluster and starting over.
