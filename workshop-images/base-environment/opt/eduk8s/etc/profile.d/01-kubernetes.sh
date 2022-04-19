# Read in Kubernetes environment variables set from setup script.

if [ -f $HOME/.local/share/workshop/kubernetes-settings.sh ]; then
    . $HOME/.local/share/workshop/kubernetes-settings.sh
fi
