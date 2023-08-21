Secret Exporter
===============

The ``SecretExporter`` custom resource can set up rules for copying a single secret from the same namespace to other namespaces, but where the recipient namespace must include a corresponding ``SecretImporter`` resource. Both ``SecretExporter`` and ``SecretImporter`` are namespaced resources and thus users of a cluster could be given selective ability via RBAC to use them in a namespace.

The raw custom resource definition for the ``SecretExporter`` custom resource can be viewed by running:

```shell
kubectl get crd/secretexporters.secrets.educates.dev -o yaml
```

Pairing of exporter and importer
--------------------------------

The ``SecretExporter`` custom resource instance must have the same name as the secret you want to export to other namespaces.

The ``SecretExporter`` must include a set of rules which stipulate which other namespaces the secret can be exported to.

Although not necessarily recommended, a ``SecretExporter`` can declare a rule which denotes that a secret should be exported to all other namespaces.

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

Secrets will never be copied into the same namespace they originated from.

No matter whether a single namespace or all is targeted, the secret will not be copied to the target namespace unless a ``SecretImporter`` custom resource instance of the same name as the target secret exists. Further, the ``SecretExporter`` and ``SecretImporter`` custom resources must include the same shared secret value to authorize that copying of the secret between the namespaces is allowed.

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

The shared secret value is mandatory to avoid the risk that if a ``SecretImporter`` is created that targets namespaces it shouldn't, that someone else in control of one of the targeted namespaces can steal the secret. For someone to be able to get a copy of the secret, they would need to know the shared secret value.

Changing the target secret name
-------------------------------

To change the name of the secret when copied to the target namespace, set ``targetSecret.name``.

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
    targetSecret:
      name: copy-of-registry-credentials
```

The name of the ``SecretImporter`` must now match the new secret name.

The secret will still never be copied into the same namespace even though the name is different.

Adding labels to the target secret
----------------------------------

Labels which may exist on the source secret are not copied to the target secret as doing so may cause issues with software which is triggered based on the presence of any labels.

To specify labels that should be applied to the secret when copied to the target namespace set ``targetSecret.labels``.

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
    targetSecret:
      labels:
        registry-pull-secret: ""
```

Limiting set of target namespaces
---------------------------------

To limit the set of target namespaces based on name, set ``targetNamespaces.nameSelector``.

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
        - example-1
        - example-2
    copyAuthorization:
      sharedSecret: my-shared-secret
```

The list of names can be the exact value, or you can also use a shell style glob expression to match a set of names.

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
        - example-*
    copyAuthorization:
      sharedSecret: my-shared-secret
```

Alternatively, you can match on labels on the namespace by setting a ``targetNamespaces.labelSelector.matchLabels``.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretExporter
metadata:
  name: registry-credentials
  namespace: registry
spec:
  rules:
  - targetNamespaces:
      labelSelector:
        matchLabels:
          developer-namespace: ""
    copyAuthorization:
      sharedSecret: my-shared-secret
```

Or if more flexible matching of labels is required, you can supply a list of expressions by setting ``targetNamespaces.labelSelector.matchExpressions``.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretExporter
metadata:
  name: registry-credentials
  namespace: registry
spec:
  rules:
  - targetNamespaces:
      labelSelector:
        matchExpressions:
        - key: developer-namespace
          operator: In
          values:
          - ""
    copyAuthorization:
      sharedSecret: my-shared-secret
```

For an expression the list of operators is `In`, `NotIn`, `Exists` and `DoesNotExist`. For `In` and `NotIn` a non empty list of values must be supplied. The `Exists` and `DoesNotExist` only pertain to the existance of the label key.

When targeting a specific namespace and the namespace is deleted, then recreated, the rule will still match the new instance of the namespace if selectors match the new instance of the namespace, even though it may notionally be used for a different purpose and the secret shouldn't be copied there.

If you need to ensure that a secret is only copied to that specific instance of the namespace, and not a future version of the namespace created subsequent to its deletion, you can require the namespace have a specific `uid` by setting `targetNamespaces.uidSelector`.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretExporter
metadata:
  name: registry-credentials
  namespace: registry
spec:
  rules:
  - targetNamespaces:
      uidSelector:
        matchUIDs:
        - 9b030c48-b773-4ffb-9d8f-7eacf7dbcfbe
    copyAuthorization:
      sharedSecret: my-shared-secret
```

The `uid` should be that set by Kubernetes in the `metadata` section of the namespace resource.

Alternatively, you can restrict whether the secret should be copied to a specific instance of a namespace based on whether that resource is owned by another. This can be done by providing the details of the owner by setting `targetNamespaces.ownerSelector`.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretExporter
metadata:
  name: registry-credentials
  namespace: registry
spec:
  rules:
  - targetNamespaces:
      ownerSelector:
        matchOwners:
        - apiVersion: training.educates.dev/v1beta1
          kind: WorkshopSession
          name: educates-cli-w01-s001
          uid: dcc4cf0f-6774-4eb4-bbf7-77a4ecaefa42
    copyAuthorization:
      sharedSecret: my-shared-secret
```

Kubernetes reserved namespaces
------------------------------

Although a corresponding ``SecretImporter`` is always required for a ``SecretExporter``, as well as a shared secret value to authorize that a copy is allowed to be made, when setting up a rule to copy a secret to all namespaces, it is recommended to exclude Kubernetes reserved namespaces.

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
        - "!kube-*"
    copyAuthorization:
      sharedSecret: my-shared-secret
```

That is, `kube-public`, `kube-system` or other namespaces starting with `kube-` will be excluded, they being generally reserved by Kubernetes itself. The `!` before the names indicates the namespace will be excluded.

In general, rather than relying on a rule which could result in a secret being copied to all namespaces, it is better to be selective by explicitly naming the target namespaces, or use labels to select the target namespaces.

Requirement to authorize copying
--------------------------------

As previously noted, the requirement for a shared secret value to authorize copying is to avoid the chance that someone could steal a secret exported from a different namespace. That they would have knowledge of the shared secret value given in the ``SecretExporter`` implies they have some authority to copy the secret.

Rather than explicitly require a value to be supplied from ``copyAuthorization.sharedSecret`` in the ``SecretExporter``, it is also possible to still leave out that section.

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
```

In this case, a shared secret value is still required in the corresponding ``SecretImporter``, but what should be used is the Kubernetes object ID for the ``SecretImporter`` resource.

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

Multiple target namespace selectors
-----------------------------------

More than one type of selector can be listed under `targetNamespaces`, in which case all selectors must match else the secret will not be copied to the namespace.

Deletion of the target secret
-----------------------------

The operator does not by default delete secrets previously copied to a namespace if the original secret is deleted or the rules defined in the ``SecretExporter`` change such that it wouldn't have been copied in the first place.

When a secret is copied into a namespace due to use of paired ``SecretExporter`` and ``SecretImporter``, the target secret will be setup to be owned by the ``SecretImporter`` custom resource instance. If the ``SecretImporter`` custom resource instance is deleted, then the target secret will also be deleted.

Tracking the source of a secret
-------------------------------

When secrets are copied, the copy of a secret will have the following annotation added so that it can be determined where the secret was copied from:

```
secrets.educates.dev/secret-name: namespace/name
```

The `SecretExporter` instance containing the rules which resulted in the secret being copied is recorded using the annotation:

```
secrets.educates.dev/copier-rule: secretexporter/name
```
