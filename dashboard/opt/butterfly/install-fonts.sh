#!/bin/bash

set -x

set -eo pipefail

curl -s -L -o /tmp/fonts.tar.gz \
    https://github.com/powerline/fonts/archive/master.tar.gz

mkdir powerline

tar --strip-components 1 -C powerline -xf /tmp/fonts.tar.gz

rm /tmp/fonts.tar.gz

mkdir -p static/fonts

cd static/fonts

FONTS="../../powerline/SourceCodePro"

ln -s "$FONTS/Source Code Pro Black for Powerline.otf" SourceCodePro-Black.otf
ln -s "$FONTS/Source Code Pro Bold for Powerline.otf" SourceCodePro-Bold.otf
ln -s "$FONTS/Source Code Pro ExtraLight for Powerline.otf" SourceCodePro-ExtraLight.otf
ln -s "$FONTS/Source Code Pro Light for Powerline.otf" SourceCodePro-Light.otf
ln -s "$FONTS/Source Code Pro Medium for Powerline.otf" SourceCodePro-Medium.otf
ln -s "$FONTS/Source Code Pro for Powerline.otf" SourceCodePro-Regular.otf
ln -s "$FONTS/Source Code Pro Semibold for Powerline.otf" SourceCodePro-Semibold.otf
