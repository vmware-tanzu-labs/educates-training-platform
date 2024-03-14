Namespace resource budget
=========================

For each workshop session a namespace is created in the Kubernetes cluster for use by just that session. This is to allow a workshop to create deployments in the cluster using Kubernetes resources, tools etc. If more than one namespace is required, this can be configured through the workshop definition.

By default Educates does not impose any restrictions on what resources can be consumed by applications deployed to the session namespace. Any limit will be whatever may be dictated by the Kubernetes cluster itself, which for standard Kubernetes cluster is no limits at all. This means a resource budget must be defined in the workshop definition for a workshop in order to limit how much resources can be used. This is done by [overriding](resource-budget-for-namespaces) the `session.namespaces.budget` property in the workshop definition.

```yaml
spec:
  session:
    namespaces:
      budget: medium
```

The value for the property is a t-shirt size which maps to a resource quota for the amount of memory and CPU which can be used by deployments in the session namespace, as well as dictating limit ranges and defaults for memory and CPU if deployments do not specify themselves what should be used.

Individual defaults and limit ranges specified for containers by the t-shirt can be overridden, but these cannot be changed so they fall outside of the bounds specified for the pod by the t-shirt size. It is best practice that any deployment to the session namespace set their own resource requirements in the deployment resource rather than falling back on the defaults imposed by the limit ranges.

If you need more control over the resource quotas and limit ranges the budget would be set to be `custom` with you needing to provide `LimitRange` and `ResourceQuota` resources as part of `session.objects`.

If the workshop uses secondary namespaces, the budget for these can similarly be [overridden](creating-additional-namespaces).

**Recommendations**

* Ensure that workshops specify a budget for the primary session namespace and any secondary namespaces. If they don't then a workshop user could consume all resources of the cluster.
* Ensure that if possible deployments made to the cluster from a workshop specify their own container resource requirements rather than falling back on using the default limit ranges.
* Ensure that if a workshop specifies a `custom` budget that it is providing appropriate `LimitRange` and `ResourceQuota` definitions.
* Ensure that if the session namespace is not required for a workshop, that access to the Kubernetes REST API is disabled.
