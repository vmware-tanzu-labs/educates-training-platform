Version 2.7.0
=============

New Features
------------

* Added the clickable action ``dashboard:expose-terminal`` such that a specific
  terminal session can be selected and given focus, without needing to send any
  command or text to the terminal. If the dashboard containing the terminal is
  hidden, the dashboard will first be exposed. This clickable action is
  recommended to be used in place of ``dashboard:open-dashboard`` to expose the
  ``Terminal`` dashboard tab as the latter action doesn't allow you to specify
  which terminal session should get focus.

Features Changed
----------------

* The version used for the local Kubernetes cluster has been updated to version
  1.27.

* Updated version of Miniconda used in Python workshop base image as the conda
  package resolver would fail to run when rebuilding the workshop base image
  using older version of Miniconda.

* Now set connect and server timeouts for Kubernetes REST API connections
  created by kopf based operators. This is to try and avoid reported problems of
  the operators not working on gke clusters when the number of nodes in the
  Kubernetes cluster is scaled up or down.

* The current working directory for an examiner test script is now set to the
  home directory of the workshop user. Previously it was wrongly inheriting the
  working directory of the workshop dashboard process.

* When using clickable actions that act against a specific terminal session,
  that terminal should now remain selected and keep focus such that any text
  subsequently entered manually will be directed to the terminal. In the case
  of a clickable action acting on multiple terminal sessions, the first terminal
  session will keep focus.
