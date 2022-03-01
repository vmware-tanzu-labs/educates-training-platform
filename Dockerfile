FROM fedora:35 AS builder

RUN HOME=/root && \
    INSTALL_PKGS=" \
        findutils \
        procps \
        which \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all && \
    useradd -u 1001 -g 0 -M -d /home/eduk8s eduk8s && \
    mkdir -p /home/eduk8s && \
    chown -R 1001:0 /home/eduk8s && \
    chmod -R g=u /home/eduk8s && \
    chmod g+w /etc/passwd && \
    chown 1001:0 /opt

COPY --chown=1001:0 opt/. /opt/

USER 1001

RUN curl -sL -o /tmp/code-server.tar.gz https://github.com/cdr/code-server/releases/download/v4.0.2/code-server-4.0.2-linux-amd64.tar.gz && \
    cd /opt/code-server && \
    tar -zxf /tmp/code-server.tar.gz --strip-components=1 && \
    rm /tmp/code-server.tar.gz

RUN mkdir /opt/code-server/extensions && \
    curl -sL -o /opt/code-server/extensions/humao.rest-client-0.24.6.vsix https://open-vsx.org/api/humao/rest-client/0.24.6/file/humao.rest-client-0.24.6.vsix && \
    curl -sL -o /opt/code-server/extensions/redhat.vscode-yaml-1.4.0.vsix https://open-vsx.org/api/redhat/vscode-yaml/1.4.0/file/redhat.vscode-yaml-1.4.0.vsix && \
    curl -sL -o /opt/code-server/extensions/ms-kubernetes-tools.vscode-kubernetes-tools-1.3.6.vsix https://open-vsx.org/api/ms-kubernetes-tools/vscode-kubernetes-tools/1.3.6/file/ms-kubernetes-tools.vscode-kubernetes-tools-1.3.6.vsix

COPY --chown=1001:0 home/. /home/

WORKDIR /home/eduk8s

EXPOSE 10085

COPY start.sh /

ENV PATH=$PATH:/opt/code-server/bin

CMD [ "/start.sh" ]
