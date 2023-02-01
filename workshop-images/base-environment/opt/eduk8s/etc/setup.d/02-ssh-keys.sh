#!/bin/bash

set -x
set -eo pipefail

# Don't run these steps again if we already have a SSH private key in place or
# if there are no source SSH keys available.

if [ -f $HOME/.ssh/id_rsa -o ! -f /opt/ssh-keys/private.pem ]; then
    exit 0
fi

# Copy the SSH private key file into place.

mkdir -p $HOME/.ssh

chmod 0700 $HOME/.ssh

cp /opt/ssh-keys/private.pem $HOME/.ssh/id_rsa

chmod 0600 $HOME/.ssh/id_rsa
