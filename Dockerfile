FROM fedora:31

COPY --chown=1001:0 opt/. /opt/

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.16 https://storage.googleapis.com/kubernetes-release/release/v1.16.11/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.16

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.7/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.17

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.18 https://storage.googleapis.com/kubernetes-release/release/v1.18.4/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.18

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.3/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.3 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.4/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.4 && \
    rm /tmp/oc.tar.gz

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.20.5/k9s_Linux_x86_64.tar.gz && \
    echo "12c03e2b3a3dcceda01c4296e618f825d017263c0ee7af15bb203620fa5c61a1 /tmp/k9s.tar.gz" | sha256sum --check --status && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/ytt https://github.com/k14s/ytt/releases/download/v0.28.0/ytt-linux-amd64 && \
    echo "52c36853999a378f21f9cf93a443e4d0e405965c3b7d2b8e499ed5fd8d6873ab /opt/kubernetes/bin/ytt" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/ytt

RUN curl -sL -o /opt/kubernetes/bin/kapp https://github.com/k14s/kapp/releases/download/v0.30.0/kapp-linux-amd64 && \
    echo "031020e3cd83883900695959f067d8afc64369c09d127a0ed34eeee3e264e422 /opt/kubernetes/bin/kapp" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kapp

RUN curl -sL -o /opt/kubernetes/bin/kbld https://github.com/k14s/kbld/releases/download/v0.22.0/kbld-linux-amd64 && \
    echo "eb888079b26330e71b855c3f37c8b81fe55125b9a6e26a43e9eeabfd016051d6 /opt/kubernetes/bin/kbld" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kbld

RUN curl -sL -o /opt/kubernetes/bin/kwt https://github.com/k14s/kwt/releases/download/v0.0.6/kwt-linux-amd64 && \
    echo "92a1f18be6a8dca15b7537f4cc666713b556630c20c9246b335931a9379196a0 /opt/kubernetes/bin/kwt" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kwt

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

RUN curl -sL -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.2.4-linux-amd64.tar.gz && \
    echo "8eb56cbb7d0da6b73cd8884c6607982d0be8087027b8ded01d6b2759a72e34b1 /tmp/helm.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-amd64/helm && \
    rm /tmp/helm.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/skaffold https://storage.googleapis.com/skaffold/releases/v1.11.0/skaffold-linux-amd64 && \
    echo "cb23d5c984b8da74112409c4fc959e2b8078ab69dc68d2a2c3d8ff900b28f964 /opt/kubernetes/bin/skaffold" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/skaffold

ENV PATH=/opt/kubernetes/bin:$PATH
