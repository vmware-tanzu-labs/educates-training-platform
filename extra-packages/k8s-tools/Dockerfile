FROM fedora:35 AS downloads

RUN HOME=/root && \
    INSTALL_PKGS=" \
        perl-Digest-SHA \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all

COPY --chown=1001:0 opt/. /opt/

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

RUN curl -sL -o /tmp/carvel.sh "https://raw.githubusercontent.com/vmware-tanzu/carvel/82da2bee562cdd859d8e95388d4152ae23cf91f8/site/static/install.sh" && \
    export K14SIO_INSTALL_BIN_DIR=/opt/kubernetes/bin && \
    sh -x /tmp/carvel.sh && \
    rm /tmp/carvel.sh

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

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

FROM scratch

COPY --from=downloads --chown=1001:100 /opt/. /opt/
