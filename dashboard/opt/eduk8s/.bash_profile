# Change colour of input text.

#export PS1="\e[0m[\w] $ \e[31m"
#trap 'echo -ne "\e[0m"' DEBUG

export PS1="[\w] $ "

# Enable kubectl bash completion.

source <(kubectl completion bash)

alias k=kubectl

complete -F __start_kubectl k

alias watch="watch "

# Enable oc bash completion.

source <(oc completion bash)

# Source profile provided for the workshop.

if [ -f /opt/eduk8s/workshop/profile ]; then
    source /opt/eduk8s/workshop/profile
fi

if [ -f /opt/workshop/profile ]; then
    source /opt/workshop/profile
fi

if [ -f $HOME/workshop/profile ]; then
    source $HOME/workshop/profile
fi

# Source $HOME/.bashrc profile in case used.

if [ -f $HOME/.bashrc ]; then
    source $HOME/.bashrc
fi
