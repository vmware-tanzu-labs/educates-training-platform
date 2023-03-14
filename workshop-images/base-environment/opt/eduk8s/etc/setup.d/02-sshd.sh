#!/bin/bash

# Don't run these steps again if we have already generated settings.

if [ -d /opt/sshd/sshd_config ]; then
    exit 0
fi

# Generate sshd settings.

if [ x"$ENABLE_SSHD" != x"true" ]; then
    exit 0
fi

chmod g-w $HOME

mkdir /opt/sshd

ssh-keygen -q -N "" -t dsa -f /opt/sshd/ssh_host_dsa_key
ssh-keygen -q -N "" -t rsa -b 4096 -f /opt/sshd/ssh_host_rsa_key
ssh-keygen -q -N "" -t ecdsa -f /opt/sshd/ssh_host_ecdsa_key
ssh-keygen -q -N "" -t ed25519 -f /opt/sshd/ssh_host_ed25519_key

cat > /opt/sshd/sshd_config << EOF
Port 2022
HostKey /opt/sshd/ssh_host_rsa_key
HostKey /opt/sshd/ssh_host_ecdsa_key
HostKey /opt/sshd/ssh_host_ed25519_key
LogLevel DEBUG3
ChallengeResponseAuthentication no
UsePAM no
PasswordAuthentication no
X11Forwarding no
PrintMotd no
PidFile /opt/sshd/sshd.pid
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

chmod 600 /opt/sshd/*
