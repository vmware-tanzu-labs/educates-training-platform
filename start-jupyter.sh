#!/bin/bash
source $HOME/.bashrc

if [ ! -f $HOME/.condarc ]; then
    cat > $HOME/.condarc << EOF
envs_dirs:
  - $HOME/.conda/envs
EOF
fi

if [ -d $HOME/.conda/envs/workspace ]; then
    echo "Activate virtual environment 'workspace'."
    conda activate workspace
fi

if [ ! -f $HOME/.jupyter/jupyter_notebook_config.json ]; then
    mkdir -p $HOME/.jupyter
    cat > $HOME/.jupyter/jupyter_notebook_config.json << EOF
{
  "NotebookApp": {
    "password": "sha1:1c5cec6a0e25:fc2cc26cf297f0760a49957bb570be0f06c525f0"
  }
}
EOF
fi

exec jupyter lab --ip 0.0.0.0 --port 8888
