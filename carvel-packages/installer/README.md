# Educates enabled cluster installer

Installs educates and all the required software on top of a Kubernetes cluster with minimal configuration.

## Test

```
ytt --data-values-file scenarios/kind/test-kind-scenario-01/values.yaml -f bundle/config | kapp deploy -a label:app=educates-installer.app -n educates-installer -f - -c -y
```

## View config

```
ytt --data-value-yaml debug=true --data-values-file scenarios/kind/test-kind-scenario-01/values.yaml -f config/ytt
```
