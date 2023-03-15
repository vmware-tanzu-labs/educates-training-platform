# Set the REGISTRY_AUTH_FILE environment variable in case that is required by
# any docker tools.

if [ x"$ENABLE_REGISTRY" != x"true" ]; then
    return
fi

REGISTRY_AUTH_FILE=$HOME/.docker/config.json

export REGISTRY_AUTH_FILE
