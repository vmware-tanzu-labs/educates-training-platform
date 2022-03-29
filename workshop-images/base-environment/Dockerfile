ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM kubernetesui/dashboard:v2.5.1 AS k8s-console

FROM ${IMAGE_REPOSITORY}/pkgs-code-server:220303.004857.8643381 AS code-server
FROM ${IMAGE_REPOSITORY}/pkgs-k8s-tools:220225.064249.5fda62b AS k8s-tools

FROM ${IMAGE_REPOSITORY}/eduk8s-vscode-helper:220303.031255.c0cb35d AS vscode-helper

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

FROM system-base AS scratch-image

COPY --from=k8s-console / /opt/console/

COPY --from=code-server /opt/. /opt/
COPY --from=code-server /home/. /home/

COPY --from=vscode-helper /opt/code-server/. /opt/code-server/
COPY --from=vscode-helper /opt/eduk8s/workshop/. /opt/eduk8s/workshop/

COPY --from=k8s-tools /opt/. /opt/.

RUN curl -sL -o /usr/local/bin/bombardier https://github.com/codesenberg/bombardier/releases/download/v1.2.5/bombardier-linux-amd64 && \
    echo "0a8338f93a2cfa7686c0c5836f6ab7ad65275e483fbf517df46df4d306682cc2 /usr/local/bin/bombardier" | sha256sum --check --status && \
    chmod +x /usr/local/bin/bombardier

RUN curl -sL -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v4.20.2/yq_linux_amd64 && \
    echo "3fbb76eaf00c3639468eb2613a6fa21933b53744e0918c4b12cdf4e1c6788de3 /usr/local/bin/yq" | sha256sum --check --status && \
    chmod +x /usr/local/bin/yq

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

RUN rm /etc/supervisord.conf && \
    ln -s /opt/eduk8s/etc/supervisord.conf /etc/supervisord.conf

RUN fix-permissions /home/eduk8s

ENV HOME=/home/eduk8s \
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/kubernetes/bin:/opt/code-server/bin:$PATH

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
