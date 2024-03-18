Docker resource requirements
============================

When docker support is enabled a dockerd instance (`dind` - docker in docker) is run as a side car container to the workshop container. When building and/or running docker images within the workshop, this is done inside of the context of this side car container and not in the main workshop container. This is the same if using tools such as `pack` which although it doesn't use the docker command, does connect to the dockerd instance running in the side car container to do the actual work.

To ensure that building and/or running container images doesn't impact on the memory availability for the workshop container, the dockerd side car is given its own separate memory allocation. By default the amount of memory is 768Mi and this memory amount is guaranteed. If running docker builds which require a lot of memory (Java and NodeJS builds), you may need to increase the memory given to the dockerd side car container. This can be [overridden](enabling-ability-to-use-docker) in the workshop definition using the `session.applications.docker.memory` setting.

```yaml
spec:
  session:
    applications:
      docker:
        enabled: true
        memory: 1Gi
```

Because of possible large transient filesystem space requirements when building container images, as well as the space required to store the built container image, or any container image pulled down into the local dockerd instance, a persistent volume is always allocated for the dockerd container. This avoids the problem that you might run out of space on the Kubernetes node were lots of workshop instances running at the same time, but depending on how large the container images are, or how much transient space is required to build a container image, you may need to increase the amount of storage. By default the amount of storage given to dockerd is 5Gi. This can be [overridden](enabling-ability-to-use-docker) in the workshop definition using the `session.applications.docker.storage` setting.

```
spec:
  session:
    applications:
      docker:
        enabled: true
        storage: 20Gi
```

**Recommendations**

* Ensure that docker support is not enabled if not being used because of additional resource requirements but also the security risks implicit in allowing dockerd to be run.
* Ensure that adequate memory is allocated to the dockerd side car container.
* Ensure that adequate storage space is allocated to the dockerd side car container.
* Ensure that the number of container images pulled down using docker is limited to what is required.
* Ensure that you don't encourage running successive builds as each change will result in more container layers being stored.
* Ensure that users are asked to delete container images to free up storage space if they can, before proceeding with subsequent workshop steps, rather than just allocating more storage space.
* Ensure that users are asked to delete stopped containers to free up storage space if they can, before proceeding with subsequent workshop steps, rather than just allocating more storage space. Alternatively, use the `-rm` option to `docker run` to ensure that stopped containers are automatically deleted when they exit.

**Related Issues**

Note that memory and storage requirements for the dockerd side car container should be added to the memory and storage requirements of the main workshop container when determining resource requirements for each workshop instance. In the case of memory, since both containers are in the same pod, the combined memory requirement has to be available on a node before a workshop instance can be scheduled to the node. For storage, a separate persistent volume claim is used for the dockerd side car container, but because it is part of the same pod as the main workshop container, a node has to have available with enough persistent volume mount points to support the combined total number of persistent volumes used.

Note that you cannot use storage space allocations that may work on local Kubernetes clusters using Kind or Minikube as a guide for how much you should use as the amount of storage requested in the case of those Kubernetes clusters is ignored and instead you can always use up to as much space as the VM or host system in which the Kubernetes cluster is running has for file system space.

Note that enabling docker support is always a risk and the Kubernetes cluster can be readily compromised by a knowledgeable person intent on mischief because dockerd has to be run using a privileged container with the user then also being able to run containers using docker as privileged. If possible avoid using docker and use methods for building container images that don't rely on docker, such as kaniko and Java native systems for building container images.

 If the only reason for using docker is to run some services for each workshop session, instead try and run them as Kubernetes services. Alternatively, use the mechanism of the docker support to run services using a docker-compose configuration snippet. Using this method will by default result in the docker socket not being exposed inside of the workshop container thus reducing the security risk.
