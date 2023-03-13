#syntax=docker/dockerfile:1.3-labs

ARG IMAGE_REPOSITORY=localhost:5001
ARG BASE_IMAGE_NAME=educates-base-environment
ARG PACKAGE_VERSION=latest

FROM ${IMAGE_REPOSITORY}/${BASE_IMAGE_NAME}:${PACKAGE_VERSION}

ARG TARGETARCH

ENV CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH

ENV MINICONDA_VERSION=22.11.1-1 \
    CONDA_VERSION=22.11.1

RUN <<EOF
    set -eo pipefail
    ARCHNAME_amd64=x86_64
    ARCHNAME_arm64=aarch64
    ARCHNAME=ARCHNAME_${TARGETARCH}
    CHECKSUM_amd64="00938c3534750a0e4069499baf8f4e6dc1c2e471c86a59caa0dd03f4a9269db6"
    CHECKSUM_arm64="48a96df9ff56f7421b6dd7f9f71d548023847ba918c3826059918c08326c2017"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    mkdir -p $CONDA_DIR
    cd /tmp
    curl --fail --silent -L -o install-miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-py310_${MINICONDA_VERSION}-Linux-${!ARCHNAME}.sh
    echo "${!CHECKSUM} install-miniconda.sh" | sha256sum --check --status
    /bin/bash install-miniconda.sh -f -b -p $CONDA_DIR
    rm install-miniconda.sh
    echo "conda ${CONDA_VERSION}" >> $CONDA_DIR/conda-meta/pinned
    conda config --system --prepend channels conda-forge
    conda config --system --set auto_update_conda false
    conda config --system --set show_channel_urls true
    conda config --system --set channel_priority strict
    conda list python | grep '^python ' | tr -s ' ' | cut -d '.' -f 1,2 | sed 's/$/.*/' >> $CONDA_DIR/conda-meta/pinned
    conda install --quiet --yes conda
    conda install --quiet --yes pip
    conda update --all --quiet --yes
    conda clean --all -f -y
    rm -rf /home/eduk8s/.cache/yarn
    fix-permissions $CONDA_DIR
    fix-permissions /home/eduk8s
EOF

RUN conda install --quiet --yes \
    'notebook=6.5.2' \
    'jupyterlab=3.5.3' && \
    conda clean --all -f -y && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf /home/eduk8s/.cache/yarn && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/eduk8s

COPY --chown=1001:0 opt/. /opt/

COPY --chown=1001:0 start-jupyterlab.sh /opt/conda

ENV ENABLE_JUPYTERLAB=false
