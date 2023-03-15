#!/bin/bash

# Install the VS Code extension which allows clickable actions to interact with
# the editor.

if [ x"$ENABLE_EDITOR" != x"true" ]; then
    exit 0
fi

if [ ! -d $HOME/.local/share/code-server/extensions/educates.educates-0.0.1 ]; then
    EXTENSIONS_GALLERY='{"serviceUrl": ""}' \
      code-server --install-extension /opt/eduk8s/educates-0.0.1.vsix \
      --disable-telemetry --disable-update-check --disable-file-downloads --force
fi
