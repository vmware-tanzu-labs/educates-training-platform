# Set the directory for serving files.

if [ x"$ENABLE_FILES" != x"true" ]; then
    return
fi

FILES_DIR=`workshop-definition -r "(.spec.session.applications.files.directory | select(type==\"string\"))"`

if [ x"$FILES_DIR" != x"" ]; then
    if [[ $FILES_DIR != '/*'* ]]; then
        FILES_DIR=$HOME/$FILES_DIR
    fi
else
    FILES_DIR=$HOME
fi

export FILES_DIR
