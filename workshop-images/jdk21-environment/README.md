JDK21 Environment
=================

This directory holds the source code for the workshop JDK21 environment image.

It can be used as a base image for constructing a custom workshop image which
includes workshop content, or can be used as the workshop image declared in the
workshop YAML definition, with workshop files pulled down from a GitHub
repository when the workshop session is created.

```
apiVersion: training.educates.dev/v1beta1
kind: Workshop
metadata:
  name: lab-java-workshop
spec:
  title: Java Testing
  description: Test of JDK21 environment.
  workshop:
    image: jdk21-environment:*
```
