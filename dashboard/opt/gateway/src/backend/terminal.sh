#!/bin/bash

export SHELL=/bin/bash

export PS1="[\w] $ "

cd /home/eduk8s

if [ x"$TERMINAL_HOME" != x"" ]; then
    cd $TERMINAL_HOME
fi

exec /bin/bash -il "$@"
