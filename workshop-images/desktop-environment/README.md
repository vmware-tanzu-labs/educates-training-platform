Desktop Environment
===================

This directory holds the source code for the workshop desktop environment image.

It can be used as a base image for constructing a custom workshop image which
includes workshop content, or can be used as the workshop image declared in the
workshop YAML definition, with workshop files pulled down from a GitHub
repository when the workshop session is created.

```
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-desktop-testing
spec:
  title: Desktop Testing
  description: Test of desktop environment.
  content:
    image: $(image_repository)/educates-desktop-environment:latest
  session:
    ingresses:
    - name: desktop
      port: 6080
    dashboards:
    - name: Desktop
      url: $(ingress_protocol)://desktop-$(session_namespace).$(ingress_domain)/vnc.html?resize=remote&autoconnect=true
```
