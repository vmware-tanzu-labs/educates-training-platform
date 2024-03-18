Workshop container storage
==========================

Workshops should write any files created as part of the workshop under the home directory of the workshop user. By default this directory is normal transient filesystem space within the container and as such all workshop instances running on the same Kubernetes node will be competing for whatever free disk space is made available on the node for container filesystems.

If a workshop downloads a large amount of binaries/source code into the workshop container, runs compilation steps, or downloads a large number of packages required when compiling applications (especially when using Java or NodeJS), if too many instances of a workshop are running at the same time on the Kubernetes node then you can feasibly run out of filesystem space on the node. The result of running low on filesystem space on the node can be that pods will be evicted from the node, which in the case of workshop instances would result in loss of any work and a user would need to start over.

To avoid the possibility of running out of filesystem space when a workshop requires a large amount of transient filesystem space, storage space should be allocated to the workshop container for the home directory of the workshop user. Doing this will result in a persistent volume claim being made for the amount of storage space requested and that persistent volume will be mounted on the home directory of the workshop user. Memory available to the workshop container is [overridden](mounting-a-persistent-volume) using the `session.resources.storage setting` in the workshop definition.

```yaml
spec:
  session:
    resources:
      storage: 5Gi
```

**Recommendations**

* Ensure that storage is allocated for the workshop container if the workshop produces a large amount of file data during the workshop.

**Related Issues**

Note that if using a custom workshop image which bundles required files as part of the workshop and they are in the home directory, the persistent volume will be mounted on top. To deal with this the workshop environment when storage space is requested, will run an init container which will first copy the contents of the home directory from the custom workshop image into the persistent volume. The persistent volume is then mounted on the home directory when the main container is run. This means any files under the home directory in the custom workshop image will be transparently transferred to the persistent volume for you, without you needing to do anything. Do be aware though that if there is a large amount of files to be copied, this can delay startup of the workshop session.

Note that you cannot use storage space allocations that may work on local Kubernetes clusters using Kind or Minikube as a guide for how much you should use as the amount of storage requested in the case of those Kubernetes clusters is ignored and instead you can always use up to as much space as the VM or host system in which the Kubernetes cluster is running has for file system space.

Note that for many infrastructure providers usually there is a limited number of persistent volumes that can be mounted on each node. The number of persistent volumes does not increase if the amount of memory the node has is increased, but stays the same. As a result, where persistent volumes are required for workshop instances, increasing the amount of memory per node in the cluster to pack more workshop instances into a node will not help as there may not be enough persistent volumes for the number of workshop instances that could fit in the node. As such, a general guideline is to use nodes with 32Gi of memory (rather than 64Gi), and add as many nodes as required to the Kubernetes cluster on that basis.

Note that there is always a risk that a workshop user could try and run a form of denial of service attack against a Kubernetes cluster, even when storage space is allocated, by writing large amounts of data into another writable part of the filesystem such as `/tmp`. How big of a problem this could be would depend on whether the Kubernetes cluster implements some sort of limits on how much transient container filesystem space any one container can use. If there is no limit there is the risk that the complete file system for the node allocated for container use could be used up, affecting other applications running on the same node.
