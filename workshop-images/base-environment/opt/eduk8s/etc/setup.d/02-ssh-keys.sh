#!/bin/bash

set -x
set -eo pipefail

# Don't run these steps again if we already have a SSH private key in place or
# if there are no source SSH keys available.

if [ -f $HOME/.ssh/id_rsa -o ! -f /opt/ssh-keys/id_rsa ]; then
    exit 0
fi

# Copy the SSH host private/public key files into the home directory.

mkdir -p $HOME/.ssh

chmod 0700 $HOME/.ssh

cp /opt/ssh-keys/id_rsa $HOME/.ssh/id_rsa
cp /opt/ssh-keys/id_rsa.pub $HOME/.ssh/id_rsa.pub

chmod 0600 $HOME/.ssh/id_rsa $HOME/.ssh/id_rsa.pub

cp $HOME/.ssh/id_rsa.pub $HOME/.ssh/authorized_keys

chmod 0600 $HOME/.ssh/authorized_keys
