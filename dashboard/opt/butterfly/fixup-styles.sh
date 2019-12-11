#!/bin/bash

VERSION=`python -c 'import sys; print(".".join(map(str,sys.version_info[:2])))'`

FILENAME=/opt/butterfly/lib/python$VERSION/site-packages/butterfly/static/main.css

cat << EOF >> $FILENAME

@supports (-webkit-overflow-scrolling: touch) {
    html, body {
        height: 100%;
        overflow: auto;
        overflow-x: hidden;
        -webkit-overflow-scrolling: touch;
    }
}}
EOF
