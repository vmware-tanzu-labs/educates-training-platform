FROM fedora:31

RUN HOME=/root && \
    INSTALL_PKGS=" \
        perl-Digest-SHA \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all

COPY --chown=1001:0 opt/. /opt/

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.12/bin/linux/amd64/kubectl && \
    echo "d6472a5f5d3ff125b4a1aa5cefd6197faadfb578c36f639240a04df1a71597e1 /opt/kubernetes/bin/kubectl@1.17" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.17

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.18 https://storage.googleapis.com/kubernetes-release/release/v1.18.9/bin/linux/amd64/kubectl && \
    echo "6a68756a2d3d04b4d0f52b00de6493ba2c1fcb28b32f3e4a0e99b3d9f6c4e8ed /opt/kubernetes/bin/kubectl@1.18" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.18

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.19 https://storage.googleapis.com/kubernetes-release/release/v1.19.2/bin/linux/amd64/kubectl && \
    echo "f51adfe7968ee173dbfb3dabfc10dc774983cbf8a3a7c1c75a1423b91fda6821 /opt/kubernetes/bin/kubectl@1.19" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/kubectl@1.19

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.4/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.4 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.5/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.5 && \
    rm /tmp/oc.tar.gz

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.21.4/k9s_Linux_x86_64.tar.gz && \
    echo "4aef9daebbc9c5e5af74545ed3491578b9118fa450cce25825c4d7a11a775eb5 /tmp/k9s.tar.gz" | sha256sum --check --status && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /tmp/carvel.sh "https://k14s.io/install.sh?date=20200929" && \
    export K14SIO_INSTALL_BIN_DIR=/opt/kubernetes/bin && \
    sh -x /tmp/carvel.sh && \
    rm /tmp/carvel.sh

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

RUN curl -sL -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.3.4-linux-amd64.tar.gz && \
    echo "b664632683c36446deeb85c406871590d879491e3de18978b426769e43a1e82c /tmp/helm.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-amd64/helm && \
    rm /tmp/helm.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v1.14.0/skaffold-linux-amd64 && \
    echo "19858bb180e045dba9d9f6e4b9fb36cbfffc6f70a13689dd03f76f7153013969 /opt/kubernetes/bin/skaffold" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/skaffold

RUN curl -sL -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v3.8.4/kustomize_v3.8.4_linux_amd64.tar.gz && \
    echo "194caffbdb59d8fc887488ba8fa3dce7b68ccf816737b57bde7338ca980f4912 /tmp/kustomize.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize && \
    rm /tmp/kustomize.tar.gz

ENV PATH=/opt/kubernetes/bin:$PATH
