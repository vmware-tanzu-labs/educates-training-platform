FROM kubernetesui/dashboard:v2.6.0 AS k8s-console

FROM fedora:36 AS system-base

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
        zlib-devel \
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

RUN curl -sL -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v4.25.2/yq_linux_amd64 && \
    echo "042f7462ec8378f8b0d3bac85d1b1a063b63beef5d8e3826bb2377294116ae90 /usr/local/bin/yq" | sha256sum --check --status && \
    chmod +x /usr/local/bin/yq

# Kubernetes tools.

RUN mkdir -p /opt/kubernetes/bin

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.20 https://storage.googleapis.com/kubernetes-release/release/v1.20.15/bin/linux/amd64/kubectl && \
    echo "d283552d3ef3b0fd47c08953414e1e73897a1b3f88c8a520bb2e7de4e37e96f3 /opt/kubernetes/bin/kubectl@1.20" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.20

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.21 https://storage.googleapis.com/kubernetes-release/release/v1.21.14/bin/linux/amd64/kubectl && \
    echo "0c1682493c2abd7bc5fe4ddcdb0b6e5d417aa7e067994ffeca964163a988c6ee /opt/kubernetes/bin/kubectl@1.21" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.21

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.22 https://storage.googleapis.com/kubernetes-release/release/v1.22.11/bin/linux/amd64/kubectl && \
    echo "a61c697e3c9871da7b609511248e41d9c9fb6d9e50001425876676924761586b /opt/kubernetes/bin/kubectl@1.22" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.22

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.23 https://storage.googleapis.com/kubernetes-release/release/v1.23.8/bin/linux/amd64/kubectl && \
    echo "299803a347e2e50def7740c477f0dedc69fc9e18b26b2f10e9ff84a411edb894 /opt/kubernetes/bin/kubectl@1.23" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.23

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.25.18/k9s_Linux_x86_64.tar.gz && \
    echo "d288aacc368ab6b243fc9e7ecd17b53fa34a813509c2dc3023171085db83cf9d /tmp/k9s.tar.gz" | sha256sum --check --status && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /tmp/carvel.sh "https://raw.githubusercontent.com/vmware-tanzu/carvel/5df4d478d296cdb39c3c2e2dcc9479467c65f6d0/site/static/install.sh" && \
    export K14SIO_INSTALL_BIN_DIR=/opt/kubernetes/bin && \
    sh -x /tmp/carvel.sh && \
    rm /tmp/carvel.sh

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    mv /opt/kubernetes/bin/octant /opt/kubernetes/bin/octant@0.12.1 && \
    rm -f /tmp/octant.tar.gz

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.25.1/octant_0.25.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.25.1_Linux-64bit/octant && \
    mv /opt/kubernetes/bin/octant /opt/kubernetes/bin/octant@0.25.1 && \
    ln -s octant@0.25.1 /opt/kubernetes/bin/octant@latest && \
    rm -f /tmp/octant.tar.gz

RUN curl -sL -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.9.0-linux-amd64.tar.gz && \
    echo "1484ffb0c7a608d8069470f48b88d729e88c41a1b6602f145231e8ea7b43b50a /tmp/helm.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-amd64/helm && \
    rm /tmp/helm.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v1.37.2/skaffold-linux-amd64 && \
    echo "5028755d1e8e5bd87b4185785b9c490002862bf62d75f76f45c91ff6fea0a0ab /opt/kubernetes/bin/skaffold" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/skaffold

RUN curl -sL -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v4.5.5/kustomize_v4.5.5_linux_amd64.tar.gz && \
    echo "bba81aa61dba057db1d5abeddf1e522b568b2d906ab67a5c80935e97302c8773 /tmp/kustomize.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize && \
    rm /tmp/kustomize.tar.gz

# VS Code editor and dashboard extension.

RUN mkdir /opt/editor && \
    curl -sL -o /tmp/code-server.tar.gz https://github.com/cdr/code-server/releases/download/v4.4.0/code-server-4.4.0-linux-amd64.tar.gz && \
    echo "e3dd265acb18c2230c72d19bbce619ac5c1bd800ebb26e5e169c4d613069500d /tmp/code-server.tar.gz" | sha256sum --check --status && \
    cd /opt/editor && \
    tar -zxf /tmp/code-server.tar.gz --strip-components=1 && \
    rm /tmp/code-server.tar.gz

COPY --from=vscode-helper --chown=1001:0 /opt/helper/educates-0.0.1.vsix /opt/eduk8s/educates-0.0.1.vsix

# Git server.

RUN mkdir /opt/git /opt/git/bin /opt/git/repositories && \
    curl --silent --fail -L -o /opt/git/bin/git-serve https://github.com/cirocosta/git-serve/releases/download/v0.0.5/git-serve && \
    chmod +x /opt/git/bin/git-serve

# Dashboard applications.

COPY opt/. /opt/

RUN mkdir -p /opt/slides/reveal.js/3.9.2 && \
    cd /opt/slides/reveal.js/3.9.2 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/3.9.2.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/reveal.js/4.3.1 && \
    cd /opt/slides/reveal.js/4.3.1 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/4.3.1.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/impress.js/1.1.0 && \
    cd /opt/slides/impress.js/1.1.0 && \
    curl -sL -o src.tar.gz https://github.com/impress/impress.js/archive/refs/tags/1.1.0.tar.gz && \
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
