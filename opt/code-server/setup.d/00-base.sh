#!/bin/bash

set -x

/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/humao.rest-client-0.24.6.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/redhat.vscode-yaml-1.4.0.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/ms-kubernetes-tools.vscode-kubernetes-tools-1.3.6.vsix
