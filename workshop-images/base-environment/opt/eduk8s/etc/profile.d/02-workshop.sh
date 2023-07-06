# Customize configuration for workshop renderer.
#
# TODO: If the slides configuration is made to depend on WORKSHOP_DIR this
# should be forced to be run earlier so WORKSHOP_DIR environment variable is
# visible to slides configuration.

if [ x"$ENABLE_WORKSHOP" != x"true" ]; then
    return
fi

WORKSHOP_PORT=10082

export WORKSHOP_PORT

# Work out location of the workshop content. This will be in workshop user home
# directory if mounting local directory, or is a custom workshop image but files
# were not moved to /opt/workshop. This will be /opt/workshop when moved to this
# location as part of custom workshop image or download-workshop was used.

WORKSHOP_DIR=""

if [ -d $HOME/workshop ]; then
    WORKSHOP_DIR=$HOME/workshop
else
    if [ -d /opt/workshop ]; then
        WORKSHOP_DIR=/opt/workshop
    else
        if [ -d /opt/eduk8s/workshop ]; then
            WORKSHOP_DIR=/opt/eduk8s/workshop
        fi
    fi
fi

export WORKSHOP_DIR
