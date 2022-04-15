FROM kubernetesui/dashboard:v2.5.1 AS k8s-console

FROM fedora:35 AS system-base

RUN HOME=/root && \
    INSTALL_PKGS=" \
        bash-completion \
        buildah \
        cadaver \
        containerd.io \
        docker-ce \
        docker-ce-cli \
        findutils \
        fuse3 \
        gcc \
        gcc-c++ \
        gettext \
        git \
        glibc-langpack-en \
        httpd \
        httpd-devel \
        jq \
        less \
        make \
        nano \
        nc \
        nodejs \
        perl-Digest-SHA \
        procps \
        python3 \
        python3-devel \
        python3-pip \
        python3-virtualenv \
        python3-wheel \
        redhat-rpm-config \
        siege \
        slirp4netns \
        skopeo \
        supervisor \
        sudo \
        tree \
        tmux \
        vim-enhanced \
        which \
        yarn \
    " && \
    dnf install -y dnf-plugins-core && \
    dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo && \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1 && \
    curl -sL https://rpm.nodesource.com/setup_14.x | bash - && \
    curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    curl -sL -o /tmp/dive_0.10.0_linux_amd64.rpm https://github.com/wagoodman/dive/releases/download/v0.10.0/dive_0.10.0_linux_amd64.rpm && \
    dnf install -y /tmp/dive_0.10.0_linux_amd64.rpm && \
    rm -f /tmp/dive_0.10.0_linux_amd64.rpm && \
    dnf clean -y --enablerepo='*' all && \
    sed -i.bak -e '1i auth requisite pam_deny.so' /etc/pam.d/su && \
    sed -i.bak -e 's/^%wheel/# %wheel/' /etc/sudoers && \
    echo "set enable-bracketed-paste off" >> /etc/inputrc && \
    useradd -u 1001 -g 0 -M -d /home/eduk8s eduk8s && \
    mkdir -p /home/eduk8s && \
    chown -R 1001:0 /home/eduk8s && \
    chmod -R g=u /home/eduk8s && \
    chmod g+w /etc/passwd && \
    chown 1001:0 /opt && \
    ln -s /var/run/docker/docker.sock /var/run/docker.sock

FROM system-base AS vscode-helper

COPY opt/helper /opt/helper

WORKDIR /opt/helper

RUN npm install && \
    npm run vsce-package

FROM system-base AS scratch-image

# Kubernetes web console.

COPY --from=k8s-console / /opt/console/

# Miscellaneous tools.

RUN curl -sL -o /usr/local/bin/bombardier https://github.com/codesenberg/bombardier/releases/download/v1.2.5/bombardier-linux-amd64 && \
    echo "0a8338f93a2cfa7686c0c5836f6ab7ad65275e483fbf517df46df4d306682cc2 /usr/local/bin/bombardier" | sha256sum --check --status && \
    chmod +x /usr/local/bin/bombardier

RUN curl -sL -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v4.20.2/yq_linux_amd64 && \
    echo "3fbb76eaf00c3639468eb2613a6fa21933b53744e0918c4b12cdf4e1c6788de3 /usr/local/bin/yq" | sha256sum --check --status && \
    chmod +x /usr/local/bin/yq

# Kubernetes tools.

RUN mkdir -p /opt/kubernetes/bin

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.20 https://storage.googleapis.com/kubernetes-release/release/v1.20.15/bin/linux/amd64/kubectl && \
    echo "d283552d3ef3b0fd47c08953414e1e73897a1b3f88c8a520bb2e7de4e37e96f3 /opt/kubernetes/bin/kubectl@1.20" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.20

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.21 https://storage.googleapis.com/kubernetes-release/release/v1.21.10/bin/linux/amd64/kubectl && \
    echo "24ce60269b1ffe1ca151af8bfd3905c2427ebef620bc9286484121adf29131c0 /opt/kubernetes/bin/kubectl@1.21" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.21

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.22 https://storage.googleapis.com/kubernetes-release/release/v1.22.7/bin/linux/amd64/kubectl && \
    echo "4dd14c5b61f112b73a5c9c844011a7887c4ffd6b91167ca76b67197dee54d388 /opt/kubernetes/bin/kubectl@1.22" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.22

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.23 https://storage.googleapis.com/kubernetes-release/release/v1.23.4/bin/linux/amd64/kubectl && \
    echo "3f0398d4c8a5ff633e09abd0764ed3b9091fafbe3044970108794b02731c72d6 /opt/kubernetes/bin/kubectl@1.23" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.23

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.25.18/k9s_Linux_x86_64.tar.gz && \
    echo "d288aacc368ab6b243fc9e7ecd17b53fa34a813509c2dc3023171085db83cf9d /tmp/k9s.tar.gz" | sha256sum --check --status && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /tmp/carvel.sh "https://raw.githubusercontent.com/vmware-tanzu/carvel/1cfceb1f3822219160fffede629a3a447dec3a0d/site/static/install.sh" && \
    export K14SIO_INSTALL_BIN_DIR=/opt/kubernetes/bin && \
    sh -x /tmp/carvel.sh && \
    rm /tmp/carvel.sh

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

# Latest Octant versions still don't work with restrictive RBAC so can't use them.
# RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.25.1/octant_0.25.1_Linux-64bit.tar.gz && \
#     tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.25.1_Linux-64bit/octant && \
#     rm -f /tmp/octant.tar.gz

RUN curl -sL -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.8.0-linux-amd64.tar.gz && \
    echo "8408c91e846c5b9ba15eb6b1a5a79fc22dd4d33ac6ea63388e5698d1b2320c8b /tmp/helm.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-amd64/helm && \
    rm /tmp/helm.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v1.36.0/skaffold-linux-amd64 && \
    echo "14e5545d5d9b69e3eff1fbfacaf5a9f5e8f33ceca4392bceb81eb27c69966c1a /opt/kubernetes/bin/skaffold" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/skaffold

RUN curl -sL -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v4.5.2/kustomize_v4.5.2_linux_amd64.tar.gz && \
    echo "c4215332da8da16ddeb88e218d8dceb76c85b366a5c58d012bc5ece904bf2fd0 /tmp/kustomize.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize && \
    rm /tmp/kustomize.tar.gz

# VS Code editor and dashboard extension.

RUN mkdir /opt/editor && \
    curl -sL -o /tmp/code-server.tar.gz https://github.com/cdr/code-server/releases/download/v4.2.0/code-server-4.2.0-linux-amd64.tar.gz && \
    cd /opt/editor && \
    tar -zxf /tmp/code-server.tar.gz --strip-components=1 && \
    rm /tmp/code-server.tar.gz

COPY --from=vscode-helper --chown=1001:0 /opt/helper/educates-0.0.1.vsix /opt/eduk8s/educates-0.0.1.vsix

# Dashboard applications.

COPY opt/. /opt/

RUN mkdir /opt/revealjs && \
    cd /opt/revealjs && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/3.9.2.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz

RUN cd /opt/httpd && \
    virtualenv /opt/httpd && \
    source /opt/httpd/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

RUN cd /opt/gateway && \
    npm install && \
    npm run compile && \
    npm prune --production && \
    npm cache clean --force

RUN cd /opt/renderer && \
    npm install && \
    npm run compile && \
    npm prune --production && \
    npm cache clean --force

FROM system-base

COPY --from=scratch-image --chown=1001:0 /opt/. /opt/
COPY --from=scratch-image --chown=1001:0 /home/. /home/

COPY --from=scratch-image /usr/local/. /usr/local/

COPY usr/. /usr/
COPY etc/. /etc/

COPY home/. /home/

RUN rm /etc/supervisord.conf && \
    ln -s /opt/eduk8s/etc/supervisord.conf /etc/supervisord.conf

RUN fix-permissions /home/eduk8s

ENV HOME=/home/eduk8s \
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/kubernetes/bin:/opt/editor/bin:$PATH

ENV REGISTRY_AUTH_FILE=/home/eduk8s/.docker/config.json

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

ENV BASH_ENV=/opt/eduk8s/etc/profile \
    ENV=/opt/eduk8s/etc/profile \
    PROMPT_COMMAND=". /opt/eduk8s/etc/profile"

WORKDIR /home/eduk8s

USER 1001

ENTRYPOINT [ "container-entrypoint" ]

EXPOSE 10080

CMD [ "start-container" ]
