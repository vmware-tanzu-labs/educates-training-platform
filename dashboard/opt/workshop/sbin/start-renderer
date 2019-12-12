#!/bin/bash

set -x

set -eo pipefail

if [ -f /opt/workshop/envvars/workshop.sh ]; then
    set -a
    . /opt/workshop/envvars/workshop.sh
    set +a
fi

if [ x"$DOWNLOAD_URL" != x"" ]; then
    download-workshop "$DOWNLOAD_URL" "$WORKSHOP_FILE"
fi

if [ -f /opt/app-root/envvars/workshop.sh ]; then
    set -a
    . /opt/app-root/envvars/workshop.sh
    set +a
fi

export HOME=/opt/renderer

cd $HOME

URI_ROOT_PATH=/workshop
export URI_ROOT_PATH

if [ x"$JUPYTERHUB_SERVICE_PREFIX" != x"" ]; then
    URI_ROOT_PATH=${JUPYTERHUB_SERVICE_PREFIX%/}/workshop
fi

export PORT=${PORT:-10082}

exec npm start
