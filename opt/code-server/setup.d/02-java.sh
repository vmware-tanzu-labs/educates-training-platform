#!/bin/bash

set +x

/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/Pivotal.vscode-spring-boot-1.30.0.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/redhat.java-1.3.0.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/vscjava.vscode-java-debug-0.38.0.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/vscjava.vscode-java-dependency-0.19.0.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/vscjava.vscode-java-test-0.34.1.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/vscjava.vscode-maven-0.35.0.vsix
/opt/code-server/bin/code-server --install-extension /opt/code-server/extensions/vscjava.vscode-spring-initializr-0.8.0.vsix
