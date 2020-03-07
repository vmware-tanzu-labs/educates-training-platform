Workshop Runtime
================

The workshop content can script the steps a user needs to run for a workshop. In some cases you may need to parameterize that content with information from the runtime environment. Data variables in workshop content allow this to a degree, but in some cases you may want to automate this through scripts executed in the workshop container to setup configuration files.

This is possible by supplying setup scripts which are run when the container is started. If necessary you can also run persistent background processes in the container which perform extra work for you while a workshop is being run.

Pre-defined environment variables
---------------------------------

When creating the workshop content, you can use data variables to automatically insert values corresponding to the specific workshop session or environment. Examples are the name of the namespace used for the session, and the ingress domain when creating an ingress route.

These data variables could be used to display a YAML/JSON resource file in the workshop content with values automatically filled out. You could also have executable commands which have the data variables substituted with values given as arguments to the commands.

For commands run in the shell environment, a number of pre-defined environment variables are also available which could be referenced directly.

Key environment variables are:

* ``WORKSHOP_NAMESPACE`` - The name of the namespace used for the workshop environment.
* ``SESSION_NAMESPACE`` - The name of the namespace the workshop instance is linked to and into which any deployed applications will run.
* ``INGRESS_DOMAIN`` - The host domain which should be used in the any generated hostname of ingress routes for exposing applications.
* ``INGRESS_PROTOCOL`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

Instead of having an executable command in the workshop content use:

.. code-block:: md

    ```execute
    kubectl get all -n %session_namespace%
    ```

with the value of the session namespace filled out when the page is renderer, you could use:

.. code-block:: md

    ```execute
    kubectl get all -n $SESSION_NAMESPACE
    ```

and the value of the environment variable will be inserted by the shell.

Running steps on container start
--------------------------------

To run a script which makes use of the above environment variables when the container is started, in order to perform tasks such as pre-create YAML/JSON resource definitions with values filled out, you can add an executable shell script to the ``workshop/setup.d`` directory. The name of the executable shell script must have a ``.sh`` suffix for it to be recognised and run.

Be aware that if the container is restarted, the setup script will be run again in the new container. If the shell script is performing actions against the Kubernetes REST API using ``kubectl`` or through another means, then the actions it performs need to be tolerant of being run more than once.

When using a setup script to fill out values in resource files a useful utility to use is ``envsubst``. This could be used in a setup script as follows:

.. code-block:: sh

    #!/bin/bash

    envsubst < frontend/ingress.yaml.in > frontend/ingress.yaml

A reference of the form ``${INGRESS_DOMAIN}`` in the input file will be replaced with the value of the ``INGRESS_DOMAIN`` environment variable.

Setup scripts when run will have the ``/home/eduk8s`` directory as the current working directory.

If you are creating or updating files in the file system, ensure that the workshop image is created with correct file permissions to allow updates. For more information see :ref:`container-run-as-random-user-id`.

Running background applications
-------------------------------

The setup scripts are run once on container startup. Although you could use the script to start a background application which is needed to run in the container for the life of the workshop, if that application stops it will not be restarted.

If you need to run a background application, the preferred mechanism is to integrate the management of the background application with the supervisor daemon run within the container.

To have the supervisor daemon manage the application for you, add a configuration file snippet for the supervisor daemon in the ``workshop/supervisor`` directory. This configuration file must have a ``.conf`` extension.

The form of the configuration file snippet should be:

.. code-block:: text

    [program:myapplication]
    process_name=myapplication
    command=/opt/myapplication/sbin/start-myapplication
    stdout_logfile=/proc/1/fd/1
    stdout_logfile_maxbytes=0
    redirect_stderr=true

The application should send any logging output to ``stdout`` or ``stderr``, and the configuration snippet should in turn direct log output to ``/proc/1/fd/1`` so that it is captured in the container log file.

If you need to restart or shutdown the application within the workshop interactive terminal, you can use the ``supervisorctl`` control script.
