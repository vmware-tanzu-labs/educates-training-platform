Workshop container startup
==========================

If a workshop needs to run special steps when the workshop container starts, it can provide executable shell scripts in the `workshop/setup.d` directory. These scripts will be run after the basic configuration is done for the workshop container, but before any application services or the dashboard are started. The scripts are self contained and setting environment variables in the scripts doesn't affect anything run after the scripts.

The typical use for these setup scripts is to generate custom resource files to be used in the workshop which have been pre-filled with details specific to the session, such as the name of the session names, ingress hostname to use etc.

If necessary, the setup scripts could be used to download separate application source code examples or binaries for tools required by a workshop, however, because these scripts are run during the process of starting up the workshop container and is done for every distinct workshop instance, a long running script will delay startup of the workshop container. If the scripts take too long to run, a user may think the workshop session is broken and abandon it. A long running script could also interfere with the timeout mechanisms in place to determine whether the workshop user has accessed the workshop session.

It is strongly recommended that these setup scripts not perform any action which takes more than 10 seconds. This means they are not really viable for downloading very large binary packages for tools. For example, it wouldn't be practical to download a JDK environment from a setup script. You also couldn't use them to pre-run a Java compilation.

When it is mentioned that the shell script needs to be executable, this means it must have the file execute bit set (`chmod +x`). If it is not marked as executable, it will not be run.

Any output from the setup script will be automatically appended to the file `~/.local/share/workshop/setup-scripts.log`. It is not necessary for the setup scripts to try and capture output and log it to its own log file.

**Recommendations**

* Ensure that setup scripts do not try to log their own output to a file so that the output is capture in the default log file location.
* Ensure that setup scripts only perform actions which take a short amount of time. Recommended less than 10 seconds.
* Ensure that setup scripts will not fail if run more than once as might occur if the workshop container was stopped and restarted.
* Ensure that setup scripts don't run application services in background, this is what the supervisord instance is for.

**Related issues**

Due to limitations with file permissions not being correctly preserved by `vendir` when unpacking archives, any scripts in the `workshop/setup.d` are currently being marked as executable automatically. For future compatibility such scripts should still be marked as executable in case the workaround is rolled back.
