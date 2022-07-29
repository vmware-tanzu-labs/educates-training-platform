#!/bin/bash

if [ ! -f $HOME/.condarc ]; then
    conda config --prepend envs_dirs $HOME/.conda/envs
    conda config --prepend pkgs_dirs $HOME/.conda/pkgs
fi

if [ ! -f $HOME/.jupyter/jupyter_server_config.json ]; then
    mkdir -p $HOME/.jupyter
    cat > $HOME/.jupyter/jupyter_server_config.json << 'EOF'
{
  "ServerApp": {
    "password": "argon2:$argon2id$v=19$m=10240,t=10,p=8$JZCmwQwwLK/qMvPpnWO+BQ$gfTKcrEH1YXkzRo3GWL9CLCOaWIPvKBmgOLJ1RDhvc0"
  }
}
EOF
fi
