JDK8 Environment
================

This directory holds the source code for the workshop JDK8 environment image.

It can be used as a base image for constructing a custom workshop image which
includes workshop content, or can be used as the workshop image declared in the
workshop YAML definition, with workshop files pulled down from a GitHub
repository when the workshop session is created.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-java-workshop
spec:
  title: Java Workshop
  description: Workshop on developing using Java.
  content:
    image: registry.eduk8s.svc.cluster.local:5001/jdk8-environment:master
    files: github.com/eduk8s-tests/lab-java-workshop
```
