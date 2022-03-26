#!/bin/bash
set -e
npm install
npm run vsce-package
rm -fr ~/.vscode/extensions/*eduk8s*
code --install-extension eduk8s-vscode-helper-0.0.1.vsix