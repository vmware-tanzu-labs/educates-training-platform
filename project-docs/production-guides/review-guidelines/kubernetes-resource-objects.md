Kubernetes resource objects
===========================

Within the workshop definition it is possible to declare Kubernetes resource objects which should be created common to the workshop environment instance created for the workshop. It is also possible to declare Kubernetes resource objects which should be created specific to each workshop session.

For namespaced Kubernetes resource objects listed against the workshop environment, ie., `environment.objects`, if a namespace is not specified for a resource, they are created within the common workshop environment namespace shared by all workshop sessions.

For namespaced Kubernetes resource objects listed against the workshop session, ie., `session.objects`, if a namespace is not specified for a resource, they are created within the session namespace created for that specific workshop session.

The name of the common workshop environment namespace is that of the instance of the workshop environment. The name of the namespace created for a specific workshop session has the name of the workshop session in it. As these names are unique to the workshop environment instance and workshop session respectively, there will be no conflict with other workshop environments, or workshop sessions.

If you declare cluster scoped Kubernetes resources within the workshop environment or session objects, similar to how the workshop environment and session namespaces will have a unique name, you need to name your cluster scoped objects with what would be a unique name. That is, you must not use a name for a cluster scoped Kubernetes resource object which would be the same across workshop sessions, or instances of workshop environments created for a workshop.

In the case of workshop sessions, because there can be more than one workshop session in existance for a workshop environment, it is obvious that specific workshop sessions cannot use cluster scoped Kubernetes resources using the same name.

For workshop environments attempts to create a cluster scoped Kubernetes resource object with a fixed name can also fail, as a prior workshop environment instance associated with that workshop may still exist. This can occur because a training portal can deploy a new workshop environment instance for a workshop when it is modified while still allowing the prior workshop environment instance to exist, so that existing workshop sessions are given time to be completed before the workshop environment is actually deleted.

For cluster scoped Kubernetes resource objects listed in `session.objects`, to ensure uniqueness, it is recommended the name should include the `$(session_name)` data variable. For cluster scoped Kubernetes resource objects listed in `environment.objects`, the name should include the `$(environment_name)` data variable.

```yaml
spec:
  session:
    objects:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: $(session_name)-extra
  environment:
    objects:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: $(environment_name)-extra
```

**Recommendations**

* Ensure that cluster scoped Kubernetes resource objects specified in the set of environment objects, use a name which embeds the name of the workshop environment.
* Ensure that cluster scoped Kubernetes resource objects specified in the set of session objects, use a name which embeds the name of the workshop session.
* Don't use environment or session objects to create custom resource definitions in the Kubernetes cluster where the name must always be the same.
