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
* Ensure that users are asked to delete stopped containers to free up storage space if they can, before proceeding with subsequent workshop steps, rather than just allocating more storage space. Alternatively, use the -rm option to docker run to ensure that stopped containers are automatically deleted when they exit.
