#!/bin/bash

export SHELL=/bin/bash

export PS1="[\w] $ "

cd /home/eduk8s

if [ x"$TERMINAL_HOME" != x"" ]; then
    cd $TERMINAL_HOME
fi

TERMINAL_SCRIPT=

if [ -x /home/eduk8s/workshop/terminal/$TERMINAL_SESSION_ID.sh ]; then
    TERMINAL_SCRIPT=/home/eduk8s/workshop/terminal/$TERMINAL_SESSION_ID.sh
else
    if [ -x /opt/workshop/terminal/$TERMINAL_SESSION_ID.sh ]; then
        TERMINAL_SCRIPT=/opt/workshop/terminal/$TERMINAL_SESSION_ID.sh
    else
        if [ -x /opt/eduk8s/workshop/terminal/$TERMINAL_SESSION_ID.sh ]; then
            TERMINAL_SCRIPT=/opt/eduk8s/workshop/terminal/$TERMINAL_SESSION_ID.sh
        fi
    fi
fi

if [ x"$TERMINAL_SCRIPT" != x"" ]; then
    exec /bin/bash -il -c "$TERMINAL_SCRIPT"
else
    exec /bin/bash -il
fi
