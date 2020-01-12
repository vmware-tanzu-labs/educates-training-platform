FROM kubernetesui/dashboard:v2.0.0-rc1

FROM fedora:31

RUN HOME=/root && \
    INSTALL_PKGS=" \
        bash-completion \
        cadaver \
        findutils \
        gcc \
        gettext \
        git \
        glibc-langpack-en \
        httpd \
        httpd-devel \
        jq \
        less \
        nano \
        nodejs \
        procps \
        python3 \
        python3-devel \
        python3-pip \
        python3-virtualenv \
        redhat-rpm-config \
        skopeo \
        supervisor \
        sudo \
        tmux \
        which \
    " && \
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

COPY usr/. /usr/

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
