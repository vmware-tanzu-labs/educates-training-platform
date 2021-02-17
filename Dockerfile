FROM fedora:31

RUN HOME=/root && \
    INSTALL_PKGS=" \
        findutils \
        procps \
        sudo \
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

COPY --chown=1001:0 opt/. /opt/

RUN mkdir /opt/code-server && \
    chown 1001:0 /opt/code-server

USER 1001

RUN curl -sL -o /tmp/code-server.tar.gz https://github.com/cdr/code-server/releases/download/v3.5.0/code-server-3.5.0-linux-amd64.tar.gz && \
    cd /opt/code-server && \
    tar -zxf /tmp/code-server.tar.gz --strip-components=1 && \
    rm /tmp/code-server.tar.gz

RUN EXTENSIONS=" \
      humao.rest-client@0.24.3 \
      ms-kubernetes-tools.vscode-kubernetes-tools@1.2.4 \
      ms-python.python@2020.5.86806 \
      golang.go@0.22.1 \
      redhat.java@0.61.0 \
    " && \
    mkdir /opt/code-server/extensions && \
    for extension in $EXTENSIONS; do /opt/code-server/bin/code-server --extensions-dir /opt/code-server/extensions --install-extension $extension || exit 1; done && \
    rm -rf /home/eduk8s/{.config,.local}

COPY --chown=1001:0 home/. /home/

WORKDIR /home/eduk8s

EXPOSE 10085

COPY start.sh /

ENV PATH=$PATH:/opt/code-server/bin

CMD [ "/start.sh" ]
