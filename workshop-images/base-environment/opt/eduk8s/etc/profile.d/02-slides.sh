# Work out location of slides if provided. The locations might be used for same
# reasons as given for main workshop content.
#
# TODO: This should perhaps only look under the directory specified by
# WORKSHOP_DIR. Some of this should be moved into the gateway application now as
# no longer need these details in the workshop renderer.

SLIDES_DIR=""

if [ -d $HOME/workshop/slides ]; then
    SLIDES_DIR=$HOME/workshop/slides
else
    if [ -d /opt/workshop/slides ]; then
        SLIDES_DIR=/opt/workshop/slides
    fi
fi

export SLIDES_DIR

if [ x"$SLIDES_DIR" != x"" ]; then
    SLIDES_URL="$INGRESS_PROTOCOL://$SESSION_NAMESPACE.$INGRESS_DOMAIN$INGRESS_PORT_SUFFIX/slides/"
fi

export SLIDES_URL
