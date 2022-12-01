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
* ``SESSION_ID`` - A unique ID for the workshop instance within the workshop environment.
* ``SESSION_NAMESPACE`` - The name of the namespace the workshop instance is linked to and into which any deployed applications will run.
* ``INGRESS_DOMAIN`` - The host domain which should be used in the any generated hostname of ingress routes for exposing applications.
* ``INGRESS_PROTOCOL`` - The protocol (http/https) that is used for ingress routes which are created for workshops.

Instead of having an executable command in the workshop content use:

~~~text
```execute
kubectl get all -n %session_namespace%
```
~~~

with the value of the session namespace filled out when the page is renderer, you could use:

~~~text
```execute
kubectl get all -n $SESSION_NAMESPACE
```
~~~

and the value of the environment variable will be inserted by the shell.

Running steps on container start
--------------------------------

To run a script which makes use of the above environment variables when the container is started, in order to perform tasks such as pre-create YAML/JSON resource definitions with values filled out, you can add an executable shell script to the ``workshop/setup.d`` directory. The name of the executable shell script must have a ``.sh`` suffix for it to be recognised and run.

Be aware that if the container is restarted, the setup script will be run again in the new container. If the shell script is performing actions against the Kubernetes REST API using ``kubectl`` or through another means, then the actions it performs need to be tolerant of being run more than once.

When using a setup script to fill out values in resource files a useful utility to use is ``envsubst``. This could be used in a setup script as follows:

```shell
#!/bin/bash

envsubst < frontend/ingress.yaml.in > frontend/ingress.yaml
```

A reference of the form ``${INGRESS_DOMAIN}`` in the input file will be replaced with the value of the ``INGRESS_DOMAIN`` environment variable.

Setup scripts when run will have the ``/home/eduk8s`` directory as the current working directory.

If you are creating or updating files in the file system and using a custom workshop image, ensure that the workshop image is created with correct file permissions to allow updates.

Running background applications
-------------------------------

The setup scripts are run once on container startup. Although you could use the script to start a background application which is needed to run in the container for the life of the workshop, if that application stops it will not be restarted.

If you need to run a background application, the preferred mechanism is to integrate the management of the background application with the supervisor daemon run within the container.

To have the supervisor daemon manage the application for you, add a configuration file snippet for the supervisor daemon in the ``workshop/supervisor`` directory. This configuration file must have a ``.conf`` extension.

The form of the configuration file snippet should be:

~~~text
[program:myapplication]
process_name=myapplication
command=/opt/myapplication/sbin/start-myapplication
stdout_logfile=/proc/1/fd/1
stdout_logfile_maxbytes=0
redirect_stderr=true
~~~

The application should send any logging output to ``stdout`` or ``stderr``, and the configuration snippet should in turn direct log output to ``/proc/1/fd/1`` so that it is captured in the container log file.

If you need to restart or shutdown the application within the workshop interactive terminal, you can use the ``supervisorctl`` control script.

Terminal user shell environment
-------------------------------

Neither the setup scripts run when the container starts, or background applications, affect the user environment of the terminal shell. The shell environment makes use of ``bash`` and the ``$HOME/.bash_profile`` script is read to perform additional setup for the user environment. Because some default setup may be included in ``$HOME/.bash_profile``, you should not replace it as you will loose that configuration.

If you want to provide commands to initialize each shell environment, you can provide the file ``workshop/profile``. When this file exists, it would be sourced automatically when each shell environment is created.

The ``workshop/profile`` script should only be used for customizing the shell environment for the interactive terminals. That is, it should only be used for actions such as modifying the terminal prompt, setting up command line completion, or other actions which don't require more sophisticated steps to be taken, as these steps will be invoked separately for every terminal session. Any environment variables set in ``workshop/profile`` are not available when rendering workshop instructions.  

If you need to run more complicated actions, such as query the Kubernetes REST API, and set environment variables based on the results, you should instead create files in the ``workshop/profile.d`` drectory. Any script files with a ``.sh`` extension found in this directory will be executed once inline with scripts used to initialize the overall container environment. This is done after the workshop content has been downloaded and any ``profile.d`` scripts will be processed before the ``setup.d`` scripts. As the ``profile.d`` scripts are executed inline to scripts used to initialize the container environment, any environment variables set and exported from the ``profile.d`` scripts will flow through and be available for use in the ``setup.d`` scripts, rendered workshop instructions, and the terminal sessions.

Overriding terminal shell command
---------------------------------

Each terminal session will be started up using the ``bash`` terminal shell and a terminal prompt will be displayed, allowing commands to be manually entered or via clickable actions targetting the terminal session.

If you want to specify the command to be run for a terminal session, you can supply an executable shell script file in the ``workshop/terminal`` directory.

The name of the shell script file for a terminal session must be of the form ``<session>.sh``, where ``<session>`` is replaced with the name of the terminal session. The session names of the default terminals that can be configured to be displayed with the dashboard are "1", "2" and "3".

The shell script file might be used to run a terminal based application such as ``k9s``, or to create an ``ssh`` session to a remote system.

```shell
#!/bin/bash

exec k9s
```

If the command that is run exits, the terminal session will be marked as exited and you will need to reload that terminal session to start over again. Alternatively you could write the shell script file as a loop so it restarts the command you want to run if it ever exits.

```shell
#!/bin/bash

while true; do
    k9s
    sleep 1
done
```

If you still want to run an interactive shell, but want to output a banner at the start of the session with special information for the user, you can use a script file to output the banner and then run the interactive shell.

```shell
#!/bin/bash

echo
echo "Your session namespace is "$SESSION_NAMESPACE".
echo

exec bash
```
