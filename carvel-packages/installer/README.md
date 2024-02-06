# Educates enabled cluster installer

Installs educates and all the required software on top of a Kubernetes cluster with minimal configuration.

## Test

```
ytt --data-values-file scenarios/test-kind-scenario-1.yaml -f config | kapp deploy -a educates -f - -c -y
```

## View config

```
ytt --data-value-yaml debug=true --data-values-file scenarios/test-kind-scenario-1.yaml -f config/ytt
```
