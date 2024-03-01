Disabling Kubernetes access
===========================

By default, a workshop session always provides access to a namespace in the Kubernetes cluster for that session. This is so that as part of a workshop deployments can be made into the Kubernetes cluster. Usually a workshop user would only have access to the single namespace created for that session.

If the topic of a workshop is such that there is never a need for a user to be able to deploy anything to the Kubernetes cluster themselves, access to the Kubernetes REST API can be disabled for the workshop.

This is done by [setting](blocking-access-to-kubernetes) `session.namespaces.security.token.enabled` to `false` in the workshop definition, and results in the service account token not being mounted into the workshop container.

```
spec:
  session:
    namespaces:
      security:
        token:
          enabled: false
```

**Recommendations**

* Ensure that access to the Kubernetes REST API is disabled if access is not required.
