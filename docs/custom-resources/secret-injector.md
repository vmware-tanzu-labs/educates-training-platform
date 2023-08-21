Secret Injector
===============

The ``SecretInjector`` custom resource sets rules for injecting image pull secrets into service accounts.

The raw custom resource definition for the ``SecretInjector`` custom resource can be viewed by running:

```shell
kubectl get crd/secretinjectors.secrets.educates.dev -o yaml
```

Specifying the source secret
----------------------------

As the ``SecretInjector`` custom resource provides a single place for specifying rules for injecting image pull secrets into service accounts of any namespace, it is cluster scoped.

To inject the named secrets in any namespace, into all service accounts in the same namespace as the secret, set `sourceSecrets.nameSelector`.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
```

Note that nothing is done to validate the secret is of the correct type before it is added as an image pull secret in the service account.

Service account names to match
------------------------------

If you only want the secret injected into the `default` service account set `serviceAccounts.nameSelector`.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
    serviceAccounts:
      nameSelector:
        matchNames:
        - default
```

More than one service account name can be specified if required.

Filtering based on resource labels
----------------------------------

Labels can instead be used on both the source secret and service accounts using `sourceSecrets.labelSelector` and `serviceAccounts.labelSelector`.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      labelSelector:
        matchLabels:
          image-pull-secret: ""
    serviceAccounts:
      labelSelector:
        matchLabels:
          inject-image-pull-secrets: ""
```

Limiting set of target namespaces
---------------------------------

You can be selective about what namespaces injection is performed. This can be done by specifying the names of the namespaces using `targetNamespaces.nameSelector`:

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
    targetNamespaces:
      nameSelector:
        matchNames:
        - developer-1
        - developer-2
```

The list of names can be the exact value, or you can also use a shell style glob expression to match a set of names.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
    targetNamespaces:
      nameSelector:
        matchNames:
        - developer-*
```

Rather than matching namespaces by their name, you can match any labels on a namespace by setting `targetNamespaces.labelSelector.matchLabels`:

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
    targetNamespaces:
      labelSelector:
        matchLabels:
          developer-namespace: ""
```

Or if more flexible matching of labels is required, you can supply a list of expressions by setting ``targetNamespaces.labelSelector.matchExpressions``.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
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

If you need to ensure that secrets should only be injected into service accounts in context of that specific instance of the namespace, and not a future version of the namespace created subsequent to its deletion, you can require the namespace have a specific `uid` by setting `targetNamespaces.uidSelector`.

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
    targetNamespaces:
      uidSelector:
        matchUIDs:
        - 9b030c48-b773-4ffb-9d8f-7eacf7dbcfbe
```

The `uid` should be that set by Kubernetes in the `metadata` section of the namespace resource.

Kubernetes reserved namespaces
------------------------------

Although it was originally said that where no selectors are specified which target specific namespaces, that all namespaces are targeted, this isn't actually the case. Instead if no `nameSelector` is specified, it defaults to the equivalent of:

```yaml
apiVersion: secrets.educates.dev/v1beta1
kind: SecretInjector
metadata:
  name: registry-credentials
spec:
  rules:
  - sourceSecrets:
      nameSelector:
        matchNames:
        - registry-credentials
    targetNamespaces:
      nameSelector:
        matchNames:
        - !kube-*
```

That is, neither `kube-public`, `kube-system` or other namespaces starting with `kube-` will be targetted, they being generally reserved by Kubernetes itself. The `!` before the names indicates the namespace will be excluded.

If you need to target these namespaces, you will need to list them explicitly using `matchNames`, which will negate the default. When using `labelSelector` and you need to exclude certain namespaces even though it may have matching labels, you can list those namespaces in `matchNames` with the leading `!` to have them excluded. When overriding `matchNames` to list excluded namespaces, you will need to manually include the exclusion for `kube-public` and `kube-system` if necessary.

Multiple selectors for reosurces
--------------------------------

More than one type of selector can be listed under `sourceSecrets`, `serviceAccounts` and `targetNamespaces`, in which case all selectors must match else nothing will be done in respect of the secret, service account or namespace.

Multiple rules for injecting secrets
------------------------------------

The `rules` property is a list, so rules for more than one secret can be specified in the one custom resource.

Deletion of the target secret
-----------------------------

The name of a secret is not removed from the list of image pull secrets in a service account if the secret is removed or rules change meaning it would no longer have been added.
