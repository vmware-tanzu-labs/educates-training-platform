# If the shell process is created by sshd, we need to inject the environment
# variables for the workshop session.

case $(ps -o comm= -p "$PPID") in
    sshd|*/sshd)
        . /opt/eduk8s/etc/profile
        ;;
esac

# Read in shell profile files for workshop session.

. /opt/eduk8s/.bash_profile
