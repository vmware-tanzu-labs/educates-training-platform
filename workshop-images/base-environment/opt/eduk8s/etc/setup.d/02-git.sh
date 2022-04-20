#!/bin/bash

# Don't run these steps again if we have already generated settings.

if [ -f $HOME/.git-credentials ]; then
    exit 0
fi

# Set defaults for git configuration and create initialize git credentials

if [ x"$ENABLE_GIT" != x"true" ]; then
    exit 0
fi

git config --global user.email "$SESSION_NAMESPACE@git.educates.dev"
git config --global user.name "$SESSION_NAMESPACE"

git config --global init.defaultBranch main

cat > $HOME/.git-credentials << EOF
$GIT_PROTOCOL://$GIT_USERNAME:$GIT_PASSWORD@$GIT_HOST
EOF

git config --global credential.helper "store --file $HOME/.git-credentials"
