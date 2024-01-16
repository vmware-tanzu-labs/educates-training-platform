#syntax=docker/dockerfile:1.3-labs

ARG IMAGE_REPOSITORY=localhost:5001
ARG BASE_IMAGE_NAME=educates-base-environment
ARG PACKAGE_VERSION=latest

FROM ${IMAGE_REPOSITORY}/${BASE_IMAGE_NAME}:${PACKAGE_VERSION}

ARG TARGETARCH

ENV CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH

ENV MINICONDA_VERSION=23.9.0-0 \
    CONDA_VERSION=23.9.0

RUN <<EOF
    set -eo pipefail
    ARCHNAME_amd64=x86_64
    ARCHNAME_arm64=aarch64
    ARCHNAME=ARCHNAME_${TARGETARCH}
    CHECKSUM_amd64="43651393236cb8bb4219dcd429b3803a60f318e5507d8d84ca00dafa0c69f1bb"
    CHECKSUM_arm64="1242847b34b23353d429fcbcfb6586f0c373e63070ad7d6371c23ddbb577778a"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    mkdir -p $CONDA_DIR
    cd /tmp
    curl --fail --silent -L -o install-miniconda.sh "https://repo.anaconda.com/miniconda/Miniconda3-py311_${MINICONDA_VERSION}-Linux-${!ARCHNAME}.sh"
    echo "${!CHECKSUM} install-miniconda.sh" | sha256sum --check --status
    /bin/bash install-miniconda.sh -f -b -p $CONDA_DIR
    rm install-miniconda.sh
    # echo "conda ${CONDA_VERSION}" >> $CONDA_DIR/conda-meta/pinned
    conda config --system --prepend channels conda-forge
    conda config --system --set auto_update_conda false
    conda config --system --set show_channel_urls true
    conda config --system --set channel_priority strict
    conda config --system --set solver libmamba
    # conda list python | grep '^python ' | tr -s ' ' | cut -d '.' -f 1,2 | sed 's/$/.*/' >> $CONDA_DIR/conda-meta/pinned
    conda install --quiet --yes conda
    conda install --quiet --yes pip
    conda update --all --quiet --yes
    conda clean --all -f -y
    rm -rf /home/eduk8s/.cache/yarn
    fix-permissions $CONDA_DIR
    fix-permissions /home/eduk8s
EOF

RUN conda install --quiet --yes \
    'notebook=7.0.6' \
    'jupyterlab=4.0.8' && \
    conda clean --all -f -y && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf /home/eduk8s/.cache/yarn && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/eduk8s

COPY --chown=1001:0 opt/. /opt/

COPY --chown=1001:0 start-jupyterlab.sh /opt/conda

ENV ENABLE_JUPYTERLAB=false
