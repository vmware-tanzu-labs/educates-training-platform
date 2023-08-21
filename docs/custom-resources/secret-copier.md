Secret Copier
=============

The ``SecretCopier`` custom resource sets rules for the copying of secrets between namespaces. The ``SecretCopier`` is a cluster scoped resource.

The raw custom resource definition for the ``SecretCopier`` custom resource can be viewed by running:

```shell
kubectl get crd/secretcopiers.secrets.educates.dev -o yaml
```

Specifying the source secret
----------------------------

To copy a secret from the specified namespace into all other namespaces use the following.

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
```

Secrets will never be copied into the same namespace they originated from.

Changing the target secret name
-------------------------------

To change the name of the secret when copied to the target namespace, set ``targetSecret.name``.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretCopier
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecret
      name: registry-credentials
      namespace: registry
    targetSecret:
      name: copy-of-registry-credentials
```

The secret will still never be copied into the same namespace even though the name is different.

Adding labels to the target secret
----------------------------------

Labels which may exist on the source secret are not copied to the target secret as doing so may cause issues with software which is triggered based on the presence of any labels.

To specify labels that should be applied to the secret when copied to the target namespace set ``targetSecret.labels``.

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
    targetSecret:
      labels:
        registry-pull-secret: ""
```

Limiting set of target namespaces
---------------------------------

To limit the set of target namespaces based on name, set ``targetNamespaces.nameSelector``.

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
    targetNamespaces:
      nameSelector:
        matchNames:
        - example-1
        - example-2
```

The list of names can be the exact value, or you can also use a shell style glob expression to match a set of names.

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
    targetNamespaces:
      nameSelector:
        matchNames:
        - example-*
```

Alternatively, you can match on labels on the namespace by setting a ``targetNamespaces.labelSelector.matchLabels``.

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
    targetNamespaces:
      labelSelector:
        matchLabels:
          developer-namespace: ""
```

Or if more flexible matching of labels is required, you can supply a list of expressions by setting ``targetNamespaces.labelSelector.matchExpressions``.

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
    targetNamespaces:
      labelSelector:
        matchExpressions:
        - key: developer-namespace
          operator: In
          values:
          - ""
```

For an expression the list of operators is `In`, `NotIn`, `Exists` and `DoesNotExist`. For `In` and `NotIn` a non empty list of values must be supplied. The `Exists` and `DoesNotExist` only pertain to the existance of the label key.

When targeting a specific namespace and the namespace is deleted, then recreated, the rule will still match the new instance of the namespace if selectors match the new instance of the namespace, even though it may notionally be used for a different purpose and the secret shouldn't be copied there.

If you need to ensure that a secret is only copied to that specific instance of the namespace, and not a future version of the namespace created subsequent to its deletion, you can require the namespace have a specific `uid` by setting `targetNamespaces.uidSelector`.

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
    targetNamespaces:
      uidSelector:
        matchUIDs:
        - 9b030c48-b773-4ffb-9d8f-7eacf7dbcfbe
```

The `uid` should be that set by Kubernetes in the `metadata` section of the namespace resource.

Alternatively, you can restrict whether the secret should be copied to a specific instance of a namespace based on whether that resource is owned by another. This can be done by providing the details of the owner by setting `targetNamespaces.ownerSelector`.

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
    targetNamespaces:
      ownerSelector:
        matchOwners:
        - apiVersion: training.educates.dev/v1beta1
          kind: WorkshopSession
          name: educates-cli-w01-s001
          uid: dcc4cf0f-6774-4eb4-bbf7-77a4ecaefa42
```

Kubernetes reserved namespaces
------------------------------

Although it was originally said that where no selectors are specified which target specific namespaces, that all namespaces are targeted, this isn't actually the case. Instead if no `nameSelector` is specified, it defaults to the equivalent of:

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
    targetNamespaces:
      nameSelector:
        matchNames:
        - !kube-*
```

That is, neither `kube-public`, `kube-system` or other namespaces starting with `kube-` will be targeted, they being generally reserved by Kubernetes itself. The `!` before the names indicates the namespace will be excluded.

If you need to target these namespaces, you will need to list them explicitly using `matchNames`, which will negate the default. When using `labelSelector` and you need to exclude certain namespaces even though it may have matching labels, you can list those namespaces in `matchNames` with the leading `!` to have them excluded. When overriding `matchNames` to list excluded namespaces, you will need to manually include the exclusion for `kube-public` and `kube-system` if necessary.

Authorizing copying of a secret
-------------------------------

For extra control over whether a secret should be copied to a namespace, even when selectors match, a shared secret can be defined.

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

In this case the target namespace must contain an instance of the namespaced custom resource `SecretImporter`, with name the same as that which would be used for the secret were the secret copied to that namespace. The shared secret must match that set by the rule in the `SecretCopier` instance.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretImporter
metadata:
  name: registry-credentials
  namespace: target-namespace
spec:
  copyAuthorization:
    sharedSecret: my-shared-secret
```

Multiple target namespace selectors
-----------------------------------

More than one type of selector can be listed under `targetNamespaces`, in which case all selectors must match else the secret will not be copied to the namespace.

Multiple rules for copying secrets
----------------------------------

The ``rules`` property is a list, so rules related to more than one secret or set of target namespaces can be specified in the one custom resource.

Overlapping rules for target secret
-----------------------------------

If multiple rules within different ``SecretCopier`` custom resource instances target the same secret, the first ``SecretCopier`` to create the target secret will win. Only the same ``SecretCopier`` as created a target secret will be able to update the secret if the source secret changes.

Deletion of the target secret
-----------------------------

The operator does not by default delete secrets previously copied to a namespace if the original secret is deleted or the rules change such that it wouldn't have been copied in the first place.

It is possible however to have any secrets which were copied into a namespace automatically deleted if the `SecretCopier` containing the rules which allowed it to be copied is deleted. This is enabled by setting a `reclaimPolicy` of `Delete` instead of the default which is `Retain`.

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
    reclaimPolicy: Delete
```

Only secrets copied after `reclaimPolicy` was set to `Delete` will be deleted. Updating the value from `Retain` to `Delete` will not retrospectively result in secrets previously copied pertaining to that rule being deleted when the `SecretCopier` is deleted, even if the source secret were subsequently updated.

Tracking the source of a secret
-------------------------------

When secrets are copied, the copy of a secret will have the following annotation added so that it can be determined where the secret was copied from:

```
secrets.educates.dev/secret-name: namespace/name
```

The `SecretCopier` instance containing the rules which resulted in the secret being copied is recorded using the annotation:

```
secrets.educates.dev/copier-rule: secretcopier/name
```
