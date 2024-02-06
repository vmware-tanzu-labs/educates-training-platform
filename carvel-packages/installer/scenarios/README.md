# Scenarios

Scenarios we want to cover:

## Local (kind)

- Scenario 1: kind using provided domain with http
- Scenario 2: kind using provided domain with certificate provided
- Scenario 3: kind using provided domain with local CA
- Scenario 4: kind using provided domain with custom configuration (MAYBE???)

### Scenario 1: kind using provided domain with http

Create:

```
kind create-cluster test-kind-scenario-1
ytt --data-values-file scenarios/test-kind-1.yaml -f src/bundle/config | kapp deploy -a educates -f - -c -y
```

Test:

```
educates deploy-workshop -f https://github.com/vmware-tanzu-labs/lab-k8s-fundamentals/releases/latest/download/workshop.yaml
educates browse-workshops
```

Delete:

```
kind delete-cluster test-kind-scenario-1
```

### Scenario 2: kind using provided domain with certificate provided

### Scenario 3: kind using provided domain with local CA

### Scenario 4: kind using provided domain with custom configuration (MAYBE???)

## AWS (eks)

- Scenario 1: eks integrating with Route53 to create DNS records and Let's Encrypt to generate wildcard

### Scenario 1: eks integrating with Route53 to create DNS records and Let's Encrypt to generate wildcard

## User provided config (custom)
