# Customize the configuration for the web console for accessing the Kubernetes
# cluster, disabling the web console if we are not running in a Kubernetes
# cluster or a kubeconfig has not been mounted into the container.
#
# TODO: Some of this should be moved into the gateway application now as no
# longer need these details in the workshop renderer. Should use a single port
# for the console regardless of which vendor it is.

ENABLE_CONSOLE_KUBERNETES=false
ENABLE_CONSOLE_OCTANT=false

export ENABLE_CONSOLE_KUBERNETES
export ENABLE_CONSOLE_OCTANT

if [ x"$ENABLE_CONSOLE" != x"true" -o ! -f $HOME/.kube/config ]; then
    ENABLE_CONSOLE=false
    return
fi

CONSOLE_VENDOR=${CONSOLE_VENDOR:-$(workshop-definition -r '(.spec.session.applications.console.vendor // "kubernetes")')}

case $CONSOLE_VENDOR in
octant)
    ENABLE_CONSOLE_OCTANT=true
    if [ x"$DEFAULT_NAMESPACE" != x"" ]; then
        CONSOLE_URL="$INGRESS_PROTOCOL://console-$SESSION_NAMESPACE.$INGRESS_DOMAIN$INGRESS_PORT_SUFFIX/#/overview/namespace/$DEFAULT_NAMESPACE"
    else
        CONSOLE_URL="$INGRESS_PROTOCOL://console-$SESSION_NAMESPACE.$INGRESS_DOMAIN$INGRESS_PORT_SUFFIX/"
    fi
    CONSOLE_PORT=10086
    ;;
*)
    ENABLE_CONSOLE_KUBERNETES=true
    if [ x"$DEFAULT_NAMESPACE" != x"" ]; then
        CONSOLE_URL="$INGRESS_PROTOCOL://console-$SESSION_NAMESPACE.$INGRESS_DOMAIN$INGRESS_PORT_SUFFIX/#/overview?namespace=$DEFAULT_NAMESPACE"
    else
        CONSOLE_URL="$INGRESS_PROTOCOL://console-$SESSION_NAMESPACE.$INGRESS_DOMAIN$INGRESS_PORT_SUFFIX/"
    fi
    CONSOLE_PORT=10083
    ;;
esac

export CONSOLE_URL
export CONSOLE_PORT
export CONSOLE_VENDOR
