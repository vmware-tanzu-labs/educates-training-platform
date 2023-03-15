#!/bin/bash

# Don't run these steps again if we have already generated settings.

if [ -f $HOME/.docker/config.json ]; then
    exit 0
fi

# Setup access credentials for working with image registries if supplied. The
# REGISTRY_AUTH_FILE environment is set to the location of the credentials file
# via a profile.d script in case that is required by any docker tools.

if [ x"$ENABLE_REGISTRY" != x"true" ]; then
    exit 0
fi

if [ ! -f $HOME/.docker/config.json ]; then
    mkdir -p $HOME/.docker
    if [ -f /var/run/registry/config.json ]; then
        cp /var/run/registry/config.json $HOME/.docker/
    fi
fi

if [ x"$INGRESS_PROTOCOL" == x"http" ]; then
    if [ ! -f $HOME/.config/containers/registries.conf ]; then
        mkdir -p $HOME/.config/containers
        cat > $HOME/.config/containers/registries.conf << EOF
[registries.insecure]
registries = ['$REGISTRY_HOST']
EOF
    fi
fi
