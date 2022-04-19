# Read in WebDAV environment variables set from setup script.

if [ -f $HOME/.local/share/workshop/webdav-settings.sh ]; then
    . $HOME/.local/share/workshop/webdav-settings.sh
fi
