#!/bin/bash

# Two usese supported:

# 1) paste at line number
curl 'http://localhost:10011/editor/paste?file=/home/kdvolder/git/kdvolder/eduk8s-vscode-helper/src/extension.ts&line=37&paste=%2F%2F%20Hello%20from%20pasty%21%0A'

# 2) paste after a given line of text (searches that line in the editor then pastes text just after it)
curl 'http://localhost:10011/editor/paste?file=/home/kdvolder/git/kdvolder/eduk8s-vscode-helper/src/extension.ts&prefix=export%20function%20activate%28context%3A%20vscode.ExtensionContext%29%20%7B&paste=%2F%2F%20Hello%20from%20pasty%21%0A'