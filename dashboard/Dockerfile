FROM kubernetesui/dashboard:v2.0.0-rc7

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
        redhat-rpm-config \
        runc \
        slirp4netns \
        skopeo \
        supervisor \
        sudo \
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

COPY etc/sudoers.d/. /etc/sudoers.d/

COPY usr/. /usr/

RUN sed -i.bak -e 's/# *mount_program =/mount_program = /' /etc/containers/storage.conf && \
    sed -i.bak -e 's/cgroup_manager = "systemd"/cgroup_manager = "cgroupfs"/' /usr/share/containers/libpod.conf && \
    sed -i.bak -e 's/# *events_logger = "journald"/events_logger = "file"/' /usr/share/containers/libpod.conf && \
    touch /etc/containers/nodocker

ENV BUILDAH_ISOLATION=chroot \
    REGISTRY_AUTH_FILE=/home/eduk8s/.docker/config.json

COPY --chown=1001:0 opt/. /opt/

COPY --chown=1001:0 home/. /home/

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

RUN rm /etc/supervisord.conf && \
    ln -s /opt/eduk8s/etc/supervisord.conf /etc/supervisord.conf

USER 1001

RUN curl -sL -o /opt/eduk8s/bin/kubectl-1.11 https://storage.googleapis.com/kubernetes-release/release/v1.11.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.11 && \
    curl -sL -o /opt/eduk8s/bin/kubectl-1.12 https://storage.googleapis.com/kubernetes-release/release/v1.12.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.12 && \
    curl -sL -o /opt/eduk8s/bin/kubectl-1.13 https://storage.googleapis.com/kubernetes-release/release/v1.13.12/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.13 && \
    curl -sL -o /opt/eduk8s/bin/kubectl-1.14 https://storage.googleapis.com/kubernetes-release/release/v1.14.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.14 && \
    curl -sL -o /opt/eduk8s/bin/kubectl-1.15 https://storage.googleapis.com/kubernetes-release/release/v1.15.7/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.15 && \
    curl -sL -o /opt/eduk8s/bin/kubectl-1.16 https://storage.googleapis.com/kubernetes-release/release/v1.16.4/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.16 && \
    curl -sL -o /opt/eduk8s/bin/kubectl-1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.0/bin/linux/amd64/kubectl && \
    chmod +x /opt/eduk8s/bin/kubectl-1.17

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v3/clients/3.11.156/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/eduk8s/bin/oc-3.11 && \
    rm /tmp/oc.tar.gz && \
    curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.1/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/eduk8s/bin/oc-4.1 && \
    rm /tmp/oc.tar.gz && \
    curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.2/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/eduk8s/bin/oc-4.2 && \
    rm /tmp/oc.tar.gz

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.15.1/k9s_Linux_x86_64.tar.gz && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/eduk8s/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /opt/eduk8s/bin/ytt https://github.com/k14s/ytt/releases/download/v0.27.1/ytt-linux-amd64 && \
    echo "b53674a21d99576b8d69483113e1ec73d9a3ed7381170a421c9afcf8aa551f15 /opt/eduk8s/bin/ytt" | sha256sum --check --status && \
    chmod 775 /opt/eduk8s/bin/ytt

RUN curl -sL -o /opt/eduk8s/bin/kapp https://github.com/k14s/kapp/releases/download/v0.24.0/kapp-linux-amd64 && \
    echo "044a8355c1a3aa4c9e427fc64f7074b80cb759e539771d70d38933886dbd2df4 /opt/eduk8s/bin/kapp" | sha256sum --check --status && \
    chmod 775 /opt/eduk8s/bin/kapp

RUN curl -sL -o /opt/eduk8s/bin/kbld https://github.com/k14s/kbld/releases/download/v0.20.0/kbld-linux-amd64 && \
    echo "a0e7dd4072587aa26db59a74bb2aadeee55ab5d285dd0544cb8eaff11821ed33 /opt/eduk8s/bin/kbld" | sha256sum --check --status && \
    chmod 775 /opt/eduk8s/bin/kbld

RUN curl -sL -o /opt/eduk8s/bin/kwt https://github.com/k14s/kwt/releases/download/v0.0.6/kwt-linux-amd64 && \
    echo "92a1f18be6a8dca15b7537f4cc666713b556630c20c9246b335931a9379196a0 /opt/eduk8s/bin/kwt" | sha256sum --check --status && \
    chmod 775 /opt/eduk8s/bin/kwt

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

RUN HOME=/opt/butterfly && \
    cd /opt/butterfly && \
    virtualenv /opt/butterfly && \
    source /opt/butterfly/bin/activate && \
    pip install --no-cache-dir -r requirements.txt && \
    /opt/butterfly/install-fonts.sh && \
    /opt/butterfly/fixup-styles.sh

RUN HOME=/opt/gateway && \
    cd /opt/gateway && \
    npm install --production

RUN HOME=/opt/renderer && \
    cd /opt/renderer && \
    npm install --production

RUN HOME=/opt/theia && \
    cd /opt/theia && \
    yarn && \
    yarn theia build && \
    rm -rf /opt/theia/.cache

RUN HOME=/opt/octant && \
    mkdir -p /opt/octant/bin && \
    curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.10.2/octant_0.10.2_Linux-64bit.tar.gz && \
    tar -C /opt/octant/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.10.2_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

COPY --from=0 --chown=1001:0 / /opt/console/

ENV HOME=/home/eduk8s \
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/supervisor/bin:$PATH

WORKDIR /home/eduk8s

RUN fix-permissions /home/eduk8s

ENV BASH_ENV=/opt/eduk8s/etc/profile \
    ENV=/opt/eduk8s/etc/profile \
    PROMPT_COMMAND=". /opt/eduk8s/etc/profile"

ENTRYPOINT [ "container-entrypoint" ]

EXPOSE 10080

CMD [ "start-container" ]
