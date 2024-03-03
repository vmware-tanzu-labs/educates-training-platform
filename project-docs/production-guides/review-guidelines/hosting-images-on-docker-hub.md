Hosting images on Docker Hub
============================

If a workshop uses an OCI image containing workshop instructions hosted on Docker Hub, or enables use of docker support and the workshop instructions have a user pull an image from Docker Hub in order to run it, or an image on Docker Hub is used in a docker build, because each workshop session results in a distinct pull of the image from Docker Hub, when running many workshop instances at the same time it is inevitable that you will hit the rate limiting imposed by Docker Hub.

In the case of running docker images or using them in an image build, in order to avoid being rate limited it is necessary to configure the Educates system to mirror images pulled by dockerd by enabling an [image registry pull through cache](image-registry-pull-through-cache) for Docker Hub. This though is not something that can be configured in the workshop definition itself and needs to be enabled for the whole Educates system on that cluster.

It is important that when setting up the mirror registry that you configure it with credentials for a Docker Hub account to ensure a greater rate limit is applied. Better still, ensure that the account is a paid account to access a greater limit again or that there is no limit at all depending on type of paid account. Anonymous access or a free account is not going to guarantee that you will not still be rate limited when many different workshops are running on the same Kubernetes cluster and they are all using container images from Docker Hub.

When enabled, an image registry mirror will be setup for each distinct workshop where docker support is enabled. It is not a single mirror registry for all workshops on the cluster as it is too hard to determine how much storage space should be allocated for the mirror registry if there is just the one.

For storage, the mirror registry for a specific workshop will be configured to use the same amount of storage that the dockerd side car container is configured to use, defaulting to 5Gi. For memory, the mirror registry for a specific workshop will be configured to the same amount of memory that the dockerd side car container is configured to use, defaulting to 768Mi. This is on the presumption that since images are being pulled down and will end up being stored in the storage associated with the dockerd side car container, that it should be enough for the mirror registry also.

The mirror registry only covers images pulled through the dockerd side car container. It does not come into play if deployments to the Kubernetes cluster directly reference images from Docker Hub. In this case container images pulled from Docker Hub would get cached on the nodes in the cluster, but if the cluster as a whole is seen as a single IP address you are still likely to get rate limited when there are many workshops deployed to the one cluster. To avoid this problem, don't use container images from Docker Hub, or, enable docker support plus a per workshop session image registry. If workshop instructions have users use docker pull to pull the container image to the local dockerd, then push the container image to the per workshop session image registry. The deployment in Kubernetes should then be setup to reference the container image from the per workshop session image registry. By pulling down the image in this way, the image will be pulled through the mirror registry only once for that workshop and not for every session.

A further problematic case for container images stored on Docker Hub is that of custom workshop images. As these are deployments to the Kubernetes cluster, they are pulled direct from Docker Hub and will be subject to rate limiting as well. Custom workshop images which reside on Docker Hub would ideally be re-hosted on a different image registry and used from there when referenced from a workshop definition.

An alternative to using a mirror registry linked to dockerd, with everything happening transparently, is to configure a [shared OCI image cache](shared-oci-image-cache) local to the workshop environment to cache the custom workshop image, with it only needing to be pulled from Docker Hub the one time and all other pulls being to the local cache. This does mean adjusting image references to explicitly use the shared OCI image cache. The shared OCI image cache can also be used with other upstream image registries besides Docker Hub, however, mirroring of images from private upstream image registries, or where credentials are required such as is the case with Docker Hub to enable a higher pull limits, is not supported. A benefit of using the shared OCI image cache is however that it can be used with OCI images holding workshop instructions and is not limited to traditional docker images.

Whether for running, in builds with dockerd, or for deployment to the cluster, any container images should always use an unchanging fixed version. Workshop instructions or deployment resources should never use versions tags such as `main`, `master`, `develop` or `latest`, or even version tags representing a major or major/minor version (without patch level), for images pulled from Docker Hub. This is because if the container image on Docker Hub is updated but uses the same version tag, the next pull of the image can result in a new version of the image being pulled down which because it is distinct from a prior image pulled to some degree, could result in the storage for the mirror registry or local OCI image cache being filled up.

Similarly to the general case, if you can't avoid using Docker Hub custom workshop images, you should avoid using `main`, `master`, `develop` and `latest` version tags for a custom workshop image. This is because doing so enables a mechanism in Educates which causes the image pull policy to be set to `Always`, meaning that an update to the image on Docker Hub would result in it being pulled down again. It is not known whether the check itself to see if there is a new version might constitute an image pull and count against the Docker Hub download count.

**Recommendations**

* Ensure that OCI images for workshop instructions are not being hosted on Docker Hub.
* Ensure that custom workshop images are not being hosted on Docker Hub.
* Ensure that support for an image registry pull through mirror is configured for the Educates system if container images are being used from Docker Hub.
* Ensure that when images are used from Docker Hub that a version tag is used for container images which guarantees that the image will not be updated.
* If possible, rather than have deployments in the cluster directly reference container images on Docker Hub, have a user pull images from Docker Hub and push them to the per workshop session image registry and deploy the container image from that registry.
* If possible just don't use container images from Docker Hub, or if can't avoid it and don't want to make users pull them down and push them to the per workshop session image registry, copy images from Docker Hub in advance to an alternate common image registry hosted in the same cluster, or elsewhere and modify workshop instructions or deployment resources to use the container images from that image registry instead. Where practical use a shared OCI image cache for the workshop environment for this purpose.

**Related Issues**

Note that if users venture beyond the workshop instructions and start pulling arbitrary container images from Docker Hub, it is possible that it can act as a denial of service attack against that workshop as storage in the mirror registry could be filled up. It is not known if the docker image registry in mirror mode will self prune images when storage is low, or whether it goes into a mode whereby it just passes requests through, thus being subject to rate limiting again. Worst case it may be necessary to manually access the pod for the mirror registry to perform commands or access REST APIs to delete images which were pulled which shouldn't be.

Note that only docker pull via the dockerd side car container is going to make use of the mirror registry. Other tools that pull image themselves, such as `dive`, `skopeo` or `imgpkg` are not going to make use of the mirror registry and would still be subject to rate limiting if using container images from Docker Hub. This is why you should not store workshop instructions/files on Docker Hub as an OCI image artefact as `imgpkg` is used in that case to pull down the OCI image artefact and unpack it at the start of every workshop session.

Note that you SHOULD NOT embed your own credentials for Docker Hub in a workshop definition and have users use that to login to Docker Hub to pull images as your credentials are obviously exposed and depending on access type they could login to the account, change the password, or otherwise cause problems.