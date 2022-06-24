Deleting Operator
=================

If you no longer need Educates, or just want to reinstall it for any reason, you can uninstall the operator. It is recommended to first check that no one is still accessing and using any of the workshop environments as their sessions will be interrupted and they will need to start over.

Deleting workshop environments
------------------------------

It is recommended to remove any workshop environments before uninstalling the Educates operator. This will ensure that everything can be cleaned up properly.

To delete all current running workshop environments run:

```
kubectl delete workshops,trainingportals,workshoprequests,workshopsessions,workshopenvironments --all
```

The Educates operator must still be running when you do this.

To make sure everything is deleted, run:

```
kubectl get workshops,trainingportals,workshoprequests,workshopsessions,workshopenvironments --all-namespaces
```

Uninstalling the operator
-------------------------

To uninstall the Educates operator, then run:

```
kubectl delete -k "github.com/eduk8s/eduk8s?ref=master"
```

This will also remove the custom resource definitions which were added, and the namespace used by Educates.
