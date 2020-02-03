Deleting eduk8s
===============

If you ever want to uninstall the eduk8s operator, first delete all current workshop environments. You can do this by running::

    kubectl delete workshops,trainingrooms,workshoprequests,workshopsessions,workshopenvironments --all

The eduk8s operator must still be running when you do this.

To make sure everything is deleted, run::

    kubectl get workshops,trainingrooms,workshoprequests,workshopsessions,workshopenvironments --all-namespaces

To uninstall the eduk8s operator, then run::

    kubectl delete -k "github.com/eduk8s/eduk8s-operator?ref=master"

This will also remove the custom resource definitions which were added, and the eduk8s namespace.
