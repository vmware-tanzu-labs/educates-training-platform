# Set the working directory for workshop exercises. The working directory for
# the editor and terminal will be changed to this directory so any extra files
# and directories in the home directory are not as visible.

EXERCISES_DIR=${EXERCISES_DIR:-exercises}

if [ -d $HOME/$EXERCISES_DIR ]; then
    TERMINAL_HOME=$HOME/$EXERCISES_DIR
    export TERMINAL_HOME

    EDITOR_HOME=$HOME/$EXERCISES_DIR
    export EDITOR_HOME
fi
