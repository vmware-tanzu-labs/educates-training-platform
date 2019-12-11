#!/bin/bash

set -eo pipefail

set -x

if [ -f /opt/workshop/envvars/terminal.sh ]; then
    set -a
    . /opt/workshop/envvars/terminal.sh
    set +a
fi

if [ -f /opt/app-root/envvars/terminal.sh ]; then
    set -a
    . /opt/app-root/envvars/terminal.sh
    set +a
fi

URI_ROOT_PATH=/terminal
export URI_ROOT_PATH

if [ x"$JUPYTERHUB_SERVICE_PREFIX" != x"" ]; then
    URI_ROOT_PATH=${JUPYTERHUB_SERVICE_PREFIX%/}/terminal
fi

# Now execute the program. We need to supply a startup script for the
# shell to setup the environment.

MOTD_FILE=motd

if [ -f /opt/workshop/etc/motd ]; then
    MOTD_FILE=/opt/workshop/etc/motd
fi

if [ -f /opt/app-root/etc/motd ]; then
    MOTD_FILE=/opt/app-root/etc/motd
fi

cd /opt/butterfly

source /opt/butterfly/bin/activate

exec butterfly.server.py --port=10081 \
    --host=0.0.0.0 --uri-root-path="$URI_ROOT_PATH" --unsecure \
    --i-hereby-declare-i-dont-want-any-security-whatsoever \
    --shell=/opt/butterfly/start-terminal.sh --motd=$MOTD_FILE
