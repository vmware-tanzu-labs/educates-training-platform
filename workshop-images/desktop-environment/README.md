Desktop Environment
===================

This directory holds the source code for the workshop desktop environment image.

It can be used as a base image for constructing a custom workshop image which
includes workshop content, or can be used as the workshop image declared in the
workshop YAML definition, with workshop files pulled down from a GitHub
repository when the workshop session is created.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-desktop-testing
spec:
  title: Desktop Testing
  description: Test of desktop environment.
  content:
    image: registry.default.svc.cluster.local:5001/desktop-environment:latest
  session:
    ingresses:
    - name: desktop
      port: 6080
    dashboards:
    - name: Desktop
      url: $(ingress_protocol)://$(session_namespace)-desktop.$(ingress_domain)$(ingress_port_suffix)/vnc.html?resize=remote&autoconnect=true
```
