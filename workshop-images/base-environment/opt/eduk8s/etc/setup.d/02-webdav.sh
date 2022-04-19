#!/bin/bash

# Setup WebDAV configuration for when running Apache.

if [ x"$ENABLE_WEBDAV" != x"true" ]; then
    exit 0
fi

mkdir -p $HOME/.webdav

WEBDAV_REALM=workshop
WEBDAV_USERFILE=$HOME/.webdav/users

WEBDAV_USERNAME=$SESSION_NAMESPACE
WEBDAV_PASSWORD=`python3 << !
import string
import random
characters = string.ascii_letters + string.digits
print("".join(random.sample(characters, 32)))
!`

(cat - | python3 > $WEBDAV_USERFILE) << !
import hashlib
dgst_md5 = hashlib.new("md5")
dgst_md5.update("$WEBDAV_USERNAME:$WEBDAV_REALM:$WEBDAV_PASSWORD".encode("utf-8"))
print("$WEBDAV_USERNAME:$WEBDAV_REALM:"+dgst_md5.hexdigest())
!

cat > $HOME/.local/share/workshop/webdav-settings.sh << EOF
export WEBDAV_REALM=$WEBDAV_REALM
export WEBDAV_USERFILE=$WEBDAV_USERFILE
export WEBDAV_USERNAME=$WEBDAV_USERNAME
export WEBDAV_PASSWORD=WEBDAV_PASSWORD
EOF
