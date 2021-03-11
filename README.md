Desktop Environment
===================

This repository contains files to build a custom workshop dashboard
container image which includes an X11 windows desktop environment. This
version of a workshop base image is provided for experimentation only.

The built contained image is hosted at:

```
quay.io/eduk8s/desktop-environment:develop
```

It can be used as a base image for constructing a custom workshop image
which includes workshop content, or can be used as the workshop image
declared in the workshop YAML definition, with workshop files pulled down
from a GitHub repository when the workshop session is created.

The X11 windows environment will be automatically started, but in order to
access it from a tab in the dashboard, you will need to add ingress and
dashboard definitions to the workshop definition.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: kubernetes-workbench
spec:
  title: Desktop Testing
  description: Test of desktop environment.
  content:
    image: quay.io/eduk8s/desktop-environment:develop
  session:
    ingresses:
    - name: desktop
      port: 6080
    dashboards:
    - name: Desktop
      url: $(ingress_protocol)://$(session_namespace)-desktop.$(ingress_domain)$(ingress_port_suffix)/vnc.html?resize=remote&autoconnect=true
```
