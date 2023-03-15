if [ x"$SSH_ENV" != x"" ]; then
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/kubernetes/bin:/opt/editor/bin:$PATH

    if [ -f $HOME/.local/share/workshop/workshop-settings.sh ]; then
        . $HOME/.local/share/workshop/workshop-settings.sh
    fi

    . $SSH_ENV

    unset SSH_ENV
fi

if [ -f /opt/eduk8s/.bash_profile ]; then
    . /opt/eduk8s/.bash_profile
fi
