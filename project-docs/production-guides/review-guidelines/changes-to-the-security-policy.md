Changes to the security policy
==============================

By default RBAC is set up for workshop session namespaces such that containers can only run as non root users due to the increased security risk of allowing workshop users to run anything as root.

In an ideal world this would be fine, but too many container images out there don't follow best practices of running as a non root user and instead will only work if run as root. This is especially the case for official images from Docker Hub.

As an example, the `nginx` image on Docker Hub, which is often used in example deployments for Kubernetes, will only run correctly if run as root.

Workshops can override the default `restricted` security policy applied through RBAC by setting the `session.namespaces.security.policy` property. Currently this can be [set](running-user-containers-as-root) to the alternative of `baseline` to allow containers to be run as root.

```
spec:
  session:
    namespaces:
      security:
        policy: baseline
```

Overall the recommended solution is not to use any container image that requires it be run as root. In the case of `nginx` one can use the `bitnami/nginx` image instead. The Bitnami catalog provides various other images as well which can run as a non root user where the official Docker Hub images will only run as root.

If absolutely necessary a workshop definition can specify its own pod security policies and bind those to a distinct service account used by a deployment to give more elevated privileges, including running as a privileged container, but this should be avoided due to the huge security risks with workshop users being able to create their own deployments using the service account and a malicious container image which could compromise the cluster.

**Recommendations**

* If possible workshops should never use container images that require they be run as root.
* Ensure that the security policy is not overridden to allow containers images to run as root if there is no need for it.
* Ensure that workshops don't give themselves elevated privileges outside of the `restricted` and `baseline` defaults, especially the ability to run privileged containers, due to the extreme security risks.

**Related Issues**

Note that when a Kubernetes virtual cluster is enabled for use with a workshop session, the security policy for the session namespace is automatically changed from `restricted` to `baseline`. This is necessary for the virtual cluster to run properly, but also means that any deployments made to the virtual cluster by a workshop user can run as the root user.
