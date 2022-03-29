Conda Environment
=================

This directory holds the source code for the workshop base environment image.

It can be used as a base image for constructing a custom workshop image which
includes workshop content, or can be used as the workshop image declared in the
workshop YAML definition, with workshop files pulled down from a GitHub
repository when the workshop session is created.

In order to have JupyterLab run, it must be enabled, and an ingress and
dashboard configured.

```
apiVersion: training.eduk8s.io/v1alpha2
kind: Workshop
metadata:
  name: lab-jupyter-workshop
spec:
  title: Jupyter Workshop
  description: Workshop on using Jupyter notebooks.
  content:
    image: registry.eduk8s.svc.cluster.local:5001/conda-environment:master
    files: github.com/eduk8s-tests/lab-jupyter-workshop
  session:
    budget: medium
    resources:
      memory: 1Gi
      storage: 5Gi
    applications:
      terminal:
        enabled: true
        layout: split
      console:
        enabled: true
      editor:
        enabled: true
        plugins:
          enabled: true
    env:
    - name: ENABLE_JUPYTERLAB
      value: "true"
    ingresses:
    - name: jupyterlab
      port: 8888
    dashboards:
    - name: JupyterLab
      url: "$(ingress_protocol)://$(session_namespace)-jupyterlab.$(ingress_domain)/
```
