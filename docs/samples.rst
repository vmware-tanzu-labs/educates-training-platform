Sample Workshop
===============

Using eduk8s there are various ways in which you could deploy and run workshops. This can be for individual learning, or for a classroom like environment if running training for many people at once. It also provides the basis for setting up and running a learning portal for on demand training.

To get a quick idea of what an eduk8s workshop environment can provide, run::

    kubectl apply -k github.com/eduk8s/lab-markdown-sample?ref=master

This will deploy a sample workshop which also provides a starter template for your own workshops.

Once deployed, run::

    kubectl get workshoprequests

This will output a list including your workshop request, with the URL it can be accessed as, and the username and password to provide when prompted by your web browser.

::

    NAME                  URL                                     USERNAME   PASSWORD
    lab-markdown-sample   http://lab-markdown-sample-8q8j1.test   eduk8s     2Jco65sDKI3q

Because this is the first time you have deployed the workshop, it can take a few moments to pull down the workshop image and start. You can monitor the progress of this workshop deployment by running::

    kubectl get all -n lab-markdown-sample

When you have finished with the workshop environment, you can run::

    kubectl delete -k github.com/eduk8s/lab-markdown-sample?ref=master
