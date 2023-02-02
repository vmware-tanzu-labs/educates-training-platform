#!/bin/bash

set -x
set -eo pipefail

# Don't run these steps again if we already have a SSH private key in place or
# if there are no source SSH keys available.

if [ -f $HOME/.ssh/id_rsa -o ! -f /opt/ssh-keys/private.pem ]; then
    exit 0
fi

# Copy the SSH private/public key file into place. We need to convert the public
# key to rsa format in the process.

mkdir -p $HOME/.ssh

chmod 0700 $HOME/.ssh

cp /opt/ssh-keys/private.pem $HOME/.ssh/id_rsa

chmod 0600 $HOME/.ssh/id_rsa

ssh-keygen -f /opt/ssh-keys/public.pem -i -m PKCS8 > $HOME/.ssh/id_rsa.pub

chmod 0600 $HOME/.ssh/id_rsa.pub
