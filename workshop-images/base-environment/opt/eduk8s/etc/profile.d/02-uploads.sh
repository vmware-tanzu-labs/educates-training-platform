# Set the directory for file uploads.

if [ x"$ENABLE_UPLOADS" != x"true" ]; then
    return
fi

UPLOADS_DIR=`workshop-definition -r "(.spec.session.applications.uploads.directory | select(type==\"string\"))"`

if [ x"$UPLOADS_DIR" != x"" ]; then
    if [[ $UPLOADS_DIR != '/*'* ]]; then
        UPLOADS_DIR=$HOME/$UPLOADS_DIR
    fi
else
    UPLOADS_DIR=$HOME
fi

UPLOADS_DIR=`realpath $UPLOADS_DIR`

mkdir -p $UPLOADS_DIR

export UPLOADS_DIR
