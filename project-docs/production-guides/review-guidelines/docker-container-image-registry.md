Docker container image registry
===============================

A workshop can enable the deployment of a container image registry per workshop session. This can be used to store container images built as part of the workshop instructions using `docker build`, `pack`, `kpack`, `kaniko` etc. The container images in the per session container image registry can then be deployed into the Kubernetes cluster.

The container image registry uses a distinct deployment separate to the deployment of the workshop instance for the session. To stores images the per session container image registry is by default given a 5Gi persistent volume. The amount of memory set aside for the container image registry defaults to 768Mi. The amount of storage and memory can
be [overridden](enabling-session-image-registry) by setting properties under `session.applications.registry` in the workshop definition.

```yaml
spec:
  session:
    applications:
      registry:
        enabled: true
        memory: 1Gi
        storage: 20Gi
```

**Recommendations**

* Ensure that adequate memory is allocated to the per session container image registry.
* Ensure that adequate storage space is allocated to the per session container image registry.
* Ensure that the workshop doesn't encourage an ongoing repetitive process of building container images and pushing them to the container image registry as this will incrementally keep using more storage as no pruning is done of old image layers.
* If possible, rather than have deployments in the cluster directly reference container images on Docker Hub, have a user pull images from Docker Hub and push them to the per workshop session image registry and deploy the container image from that registry. At the same time, ensure that use of a Docker Hub mirror for each workshop environment is configured for Educates to avoid issues with possible rate limiting by Docker Hub. Alternatively look at using a shared OCI image cache with with specific workshop environments to mirror required images.
