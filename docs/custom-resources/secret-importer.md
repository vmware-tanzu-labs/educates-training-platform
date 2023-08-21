Secret Importer
===============

The ``SecretImporter`` custom resource is required to be used in conjunction with ``SecretExporter`` and ``SecretCopier`` when necessary to provide a shared secret value in order to authorize the copying of a secret into a target namespace. The ``SecretImporter`` is namespaced and thus users of a cluster could be given selective ability via RBAC to use them in a namespace.

The raw custom resource definition for the ``SecretImporter`` custom resource can be viewed by running:

```shell
kubectl get crd/secretimporters.secrets.educates.dev -o yaml
```

Providing authorization to copy
-------------------------------

The primary purpose of the ``SecretImporter`` is to provide a shared secret value that indicates that a namespace is entitled to receive a secret exported from another namespace.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretImporter
metadata:
  name: registry-credentials
  namespace: developer-namespace
spec:
  copyAuthorization:
    sharedSecret: my-shared-secret
```

The shared secret value is mandatory so that if a ``SecretExporter`` or ``SecretCopier`` is created that targets namespaces it shouldn't, that someone else in control of one of the targeted namespaces can't steal the secret. For someone to be able to get a copy of the secret, they would need to know the shared secret value.

As such, the ``SecretImporter`` needs to use the same shared secret values as would be defined in the ``SecretExporter``:

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretExporter
metadata:
  name: registry-credentials
  namespace: registry
spec:
  rules:
  - targetNamespaces:
      nameSelector:
        matchNames:
        - "*"
    copyAuthorization:
      sharedSecret: my-shared-secret
```

or a ``SecretCopier``:

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretCopier
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecret:
      name: registry-credentials
      namespace: registry
    copyAuthorization:
      sharedSecret: my-shared-secret
```

When the rule for copying a secret is defined by a ``SecretExporter``, it is possible that it may not define a shared secret value. In this case a shared secret value is still required in the corresponding ``SecretImporter``, but what should be used is the Kubernetes object ID for the ``SecretImporter`` resource.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretImporter
metadata:
  name: registry-credentials
  namespace: developer-namespace
spec:
  copyAuthorization:
    sharedSecret: bd380bd5-4ddc-403a-bdba-454bf21bd7b3
```

That is, the shared secret value would be the ``uid`` from the ``metadata`` section of the ``SecretExporter``.

Overlapping rules for target secret
-----------------------------------

If multiple rules within different ``SecretExporter`` or ``SecretCopier`` custom resource instances target the same secret, the first to create the target secret will by default win. Only updates against the same source secret as the target secret was originally created from will later be applied.

When using ``SecretImporter`` it is possible to qualify from which namespace a source secret may be copied from when there are possible conflicts.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretImporter
metadata:
  name: registry-credentials
  namespace: developer-namespace
spec:
  sourceNamespaces:
    nameSelector:
      matchNames:
      - registry
  copyAuthorization:
    sharedSecret: my-shared-secret
```

Because secrets can be renamed in the process of being copied, this can be further qualified by identifying by name the source secret in the source namespace.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretImporter
metadata:
  name: registry-credentials
  namespace: developer-namespace
spec:
  sourceSecret:
    name: registry-credentials
  sourceNamespaces:
    nameSelector:
      matchNames:
      - registry
  copyAuthorization:
    sharedSecret: my-shared-secret
```

Deletion of the secret importer
-------------------------------

When a secret is copied into a namespace due to use of paired ``SecretExporter`` and ``SecretImporter``, the target secret will be setup to be owned by the ``SecretImporter`` custom resource instance. If the ``SecretImporter`` custom resource instance is deleted, then the target secret will also be deleted.
