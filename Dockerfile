ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM ${IMAGE_REPOSITORY}/base-environment:210331.000304.07c1f5f

ENV CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH

ENV MINICONDA_VERSION=4.8.2 \
    MINICONDA_MD5=87e77f097f6ebb5127c77662dfc3165e \
    CONDA_VERSION=4.8.2

RUN mkdir -p $CONDA_DIR && \
    cd /tmp && \
    curl -sL -o install-miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-py37_${MINICONDA_VERSION}-Linux-x86_64.sh && \
    echo "${MINICONDA_MD5} install-miniconda.sh" | md5sum -c - && \
    /bin/bash install-miniconda.sh -f -b -p $CONDA_DIR && \
    rm install-miniconda.sh && \
    echo "conda ${CONDA_VERSION}" >> $CONDA_DIR/conda-meta/pinned && \
    conda config --system --prepend channels conda-forge && \
    conda config --system --set auto_update_conda false && \
    conda config --system --set show_channel_urls true && \
    conda config --system --set channel_priority strict && \
    conda list python | grep '^python ' | tr -s ' ' | cut -d '.' -f 1,2 | sed 's/$/.*/' >> $CONDA_DIR/conda-meta/pinned && \
    conda install --quiet --yes conda && \
    conda install --quiet --yes pip && \
    conda update --all --quiet --yes && \
    conda clean --all -f -y && \
    rm -rf /home/eduk8s/.cache/yarn && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/eduk8s

RUN conda install --quiet --yes \
    'notebook=6.0.3' \
    'jupyterlab=2.0.1' && \
    conda clean --all -f -y && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf /home/eduk8s/.cache/yarn && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/eduk8s

COPY --chown=1001:0 workshop /opt/eduk8s/workshop

COPY --chown=1001:0 start-jupyterlab.sh /opt/conda

ENV ENABLE_JUPYTERLAB=false
