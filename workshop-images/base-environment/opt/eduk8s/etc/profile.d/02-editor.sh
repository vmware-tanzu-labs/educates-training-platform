# Customize configuration for embedded VS Code editor and install the VS Code
# extension which allows clickable actions to interact with the editor.

if [ x"$ENABLE_EDITOR" != x"true" ]; then
    return
fi

EDITOR_URL="$INGRESS_PROTOCOL://editor-$SESSION_NAMESPACE.$INGRESS_DOMAIN$INGRESS_PORT_SUFFIX/"
EDITOR_PORT=10085

export EDITOR_URL
export EDITOR_PORT

code-server --install-extension /opt/eduk8s/educates-0.0.1.vsix
