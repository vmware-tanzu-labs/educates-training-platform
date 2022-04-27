#!/bin/bash

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/conda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        . "/opt/conda/etc/profile.d/conda.sh"
    else
        export PATH="/opt/conda/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

if [ -d $HOME/.conda/envs/workspace ]; then
    echo "Activate virtual environment 'workspace'."
    conda activate workspace
else
    conda activate base
fi

EXERCISES_DIR=${EXERCISES_DIR:-exercises}

if [ -d $HOME/$EXERCISES_DIR ]; then
    TERMINAL_HOME=$HOME/$EXERCISES_DIR
fi

TERMINAL_HOME=${TERMINAL_HOME:-$HOME}

export TERMINAL_HOME

cd $TERMINAL_HOME

exec jupyter lab --ip 0.0.0.0 --port 8888
