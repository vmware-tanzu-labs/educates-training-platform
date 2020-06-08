ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM kubernetesui/dashboard:v2.0.0 AS k8s-console

FROM ${IMAGE_REPOSITORY}/pkgs-code-server:200607.120502.570e0c6 AS code-server
FROM ${IMAGE_REPOSITORY}/pkgs-k8s-tools:200607.054006.f0b5d22 AS k8s-tools
FROM ${IMAGE_REPOSITORY}/pkgs-butterfly:200601.023245.e90edb8 AS butterfly

FROM fedora:31

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
        nodejs \
        podman \
        procps \
        python3 \
        python3-devel \
        python3-pip \
        python3-virtualenv \
        python3-wheel \
        redhat-rpm-config \
        runc \
        slirp4netns \
        skopeo \
        supervisor \
        sudo \
        tree \
        tmux \
        which \
        yarn \
    " && \
    dnf install -y dnf-plugins-core && \
    dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo && \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1 && \
    curl -sL https://rpm.nodesource.com/setup_10.x | bash - && \
    curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all && \
    sed -i.bak -e '1i auth requisite pam_deny.so' /etc/pam.d/su && \
    sed -i.bak -e 's/^%wheel/# %wheel/' /etc/sudoers && \
    useradd -u 1001 -g 0 -M -d /home/eduk8s eduk8s && \
    mkdir -p /home/eduk8s && \
    chown -R 1001:0 /home/eduk8s && \
    chmod -R g=u /home/eduk8s && \
    chmod g+w /etc/passwd && \
    chown 1001:0 /opt

RUN sed -i.bak -e 's/# *mount_program =/mount_program = /' /etc/containers/storage.conf && \
    sed -i.bak -e 's/cgroup_manager = "systemd"/cgroup_manager = "cgroupfs"/' /usr/share/containers/libpod.conf && \
    sed -i.bak -e 's/# *events_logger = "journald"/events_logger = "file"/' /usr/share/containers/libpod.conf && \
    ln -s /var/run/docker/docker.sock /var/run/docker.sock && \
    touch /etc/containers/nodocker

ENV BUILDAH_ISOLATION=chroot \
    REGISTRY_AUTH_FILE=/home/eduk8s/.docker/config.json

COPY --from=k8s-console --chown=1001:0 / /opt/console/

COPY --from=code-server --chown=1001:0 /opt/. /opt/

COPY --from=k8s-tools --chown=1001:0 /opt/. /opt/.

COPY --from=butterfly --chown=1001:0 /opt/. /opt/.

COPY usr/. /usr/

COPY etc/. /etc/

COPY --chown=1001:0 opt/. /opt/

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

RUN rm /etc/supervisord.conf && \
    ln -s /opt/eduk8s/etc/supervisord.conf /etc/supervisord.conf

USER 1001

RUN HOME=/opt/revealjs && \
    mkdir /opt/revealjs && \
    cd /opt/revealjs && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/3.8.0.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz

RUN HOME=/opt/webdav && \
    cd /opt/webdav && \
    virtualenv /opt/webdav && \
    source /opt/webdav/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

RUN HOME=/opt/gateway && \
    cd /opt/gateway && \
    npm install --production

RUN HOME=/opt/renderer && \
    cd /opt/renderer && \
    npm install --production

ENV HOME=/home/eduk8s \
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/kubernetes/bin:/opt/code-server/bin:$PATH

WORKDIR /home/eduk8s

RUN fix-permissions /home/eduk8s

ENV BASH_ENV=/opt/eduk8s/etc/profile \
    ENV=/opt/eduk8s/etc/profile \
    PROMPT_COMMAND=". /opt/eduk8s/etc/profile"

ENTRYPOINT [ "container-entrypoint" ]

EXPOSE 10080

CMD [ "start-container" ]
