FROM fedora:31

COPY --chown=1001:0 opt/. /opt/

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.16 https://storage.googleapis.com/kubernetes-release/release/v1.16.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.16

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.6/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.17

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.18 https://storage.googleapis.com/kubernetes-release/release/v1.18.3/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.18

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.3/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.3 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.4/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.4 && \
    rm /tmp/oc.tar.gz

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.20.2/k9s_Linux_x86_64.tar.gz && \
    echo "c51be2299ba36a31cbc5ed69ad50d8b4ba8bbf4143c7104da53e2e447fee5c2b /tmp/k9s.tar.gz" | sha256sum --check --status && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/ytt https://github.com/k14s/ytt/releases/download/v0.27.2/ytt-linux-amd64 && \
    echo "64bcc36df4270e3413fd26b68683a353089c3b15c411904307e93c12f80556ab /opt/kubernetes/bin/ytt" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/ytt

RUN curl -sL -o /opt/kubernetes/bin/kapp https://github.com/k14s/kapp/releases/download/v0.27.0/kapp-linux-amd64 && \
    echo "01487d351bd1e0aac8961ab28a27bd3cb7239b587154e2bb4a10a2bdafa2b9bb /opt/kubernetes/bin/kapp" | sha256sum --check --status && \
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

ENV PATH=/opt/kubernetes/bin:$PATH
