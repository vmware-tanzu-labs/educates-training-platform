#!/bin/bash

set -eo pipefail

set -x

WEBDAV_PREFIX=${WEBDAV_PREFIX:-${JUPYTERHUB_SERVICE_PREFIX%/}}
export WEBDAV_PREFIX

WEBDAV_PORT=${WEBDAV_PORT:-10084}

ARGS=""

ARGS="$ARGS --log-to-terminal"
ARGS="$ARGS --port $WEBDAV_PORT"
ARGS="$ARGS --application-type static"
ARGS="$ARGS --include /opt/workshop/etc/httpd-webdav.conf"

cd /opt/webdav

source /opt/webdav/bin/activate

exec mod_wsgi-express start-server $ARGS
