# Enable kubectl bash completion.

source <(kubectl completion bash)

# Enable oc bash completion.

source <(oc completion bash)

# Source profile provided for the workshop.

if [ -f $HOME/workshop/profile ]; then
    source $HOME/workshop/profile
fi
