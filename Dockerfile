FROM fedora:31

RUN HOME=/root && \
    INSTALL_PKGS=" \
        perl-Digest-SHA \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all

COPY --chown=1001:0 opt/. /opt/

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.17/bin/linux/amd64/kubectl && \
    echo "8329fac94c66bf7a475b630972a8c0b036bab1f28a5584115e8dd26483de8349 /opt/kubernetes/bin/kubectl@1.17" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.17

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.18 https://storage.googleapis.com/kubernetes-release/release/v1.18.15/bin/linux/amd64/kubectl && \
    echo "eb5a5dd0a72795942ab81d1e4331625e80a90002c8bb39b2cb15aa707a3812c6 /opt/kubernetes/bin/kubectl@1.18" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.18

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.19 https://storage.googleapis.com/kubernetes-release/release/v1.19.7/bin/linux/amd64/kubectl && \
    echo "d46eb3bbe2575e5b6bedbc6d3519424b4f2f57929d7da1ef7e11c09068f37297 /opt/kubernetes/bin/kubectl@1.19" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.19

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.20 https://storage.googleapis.com/kubernetes-release/release/v1.20.2/bin/linux/amd64/kubectl && \
    echo "2583b1c9fbfc5443a722fb04cf0cc83df18e45880a2cf1f6b52d9f595c5beb88 /opt/kubernetes/bin/kubectl@1.20" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.20

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.5/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.5 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.6/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.6 && \
    rm /tmp/oc.tar.gz

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.24.2/k9s_Linux_x86_64.tar.gz && \
    echo "238b754da8469c1e25a2699d2994a59b16308b2abee671cbf9c476a0b8d9bd67 /tmp/k9s.tar.gz" | sha256sum --check --status && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /tmp/carvel.sh "https://carvel.dev/install.sh?date=20210217" && \
    export K14SIO_INSTALL_BIN_DIR=/opt/kubernetes/bin && \
    sh -x /tmp/carvel.sh && \
    rm /tmp/carvel.sh

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

RUN curl -sL -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.5.2-linux-amd64.tar.gz && \
    echo "01b317c506f8b6ad60b11b1dc3f093276bb703281cb1ae01132752253ec706a2 /tmp/helm.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-amd64/helm && \
    rm /tmp/helm.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v1.20.0/skaffold-linux-amd64 && \
    echo "725b5b5b9456cb1abc26c8a7528906e27c30980cda79249d780618c3834a7aa3 /opt/kubernetes/bin/skaffold" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/skaffold

RUN curl -sL -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v4.0.1/kustomize_v4.0.1_linux_amd64.tar.gz && \
    echo "914c006a4c00e92e09c050e5be594ef1270d47ea41b84dd7bdcab6b3b05b9297 /tmp/kustomize.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize && \
    rm /tmp/kustomize.tar.gz

ENV PATH=/opt/kubernetes/bin:$PATH
