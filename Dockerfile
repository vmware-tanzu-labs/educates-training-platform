FROM fedora:31

COPY --chown=1001:0 opt/. /opt/

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.16 https://storage.googleapis.com/kubernetes-release/release/v1.16.13/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.16

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.9/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.17

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.18 https://storage.googleapis.com/kubernetes-release/release/v1.18.6/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.18

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

RUN curl -sL -o /opt/kubernetes/bin/ytt https://github.com/k14s/ytt/releases/download/v0.28.0/ytt-linux-amd64 && \
    echo "52c36853999a378f21f9cf93a443e4d0e405965c3b7d2b8e499ed5fd8d6873ab /opt/kubernetes/bin/ytt" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/ytt

RUN curl -sL -o /opt/kubernetes/bin/kapp https://github.com/k14s/kapp/releases/download/v0.31.0/kapp-linux-amd64 && \
    echo "9039157695a2c6a6c768b21fe2550a64668251340cc17cf648d918be65ac73bd /opt/kubernetes/bin/kapp" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kapp

RUN curl -sL -o /opt/kubernetes/bin/kbld https://github.com/k14s/kbld/releases/download/v0.24.0/kbld-linux-amd64 && \
    echo "63f06c428cacd66e4ebbd23df3f04214109bc44ee623c7c81ecb9aa35c192c65 /opt/kubernetes/bin/kbld" | sha256sum --check --status && \
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

RUN curl -sL -o /opt/kubernetes/bin/skaffold https://storage.googleapis.com/skaffold/releases/v1.12.1/skaffold-linux-amd64 && \
    echo "e96db5103448663d349072c515ddae33bdf05727689a9a3460f3f36a41a94b8e /opt/kubernetes/bin/skaffold" | sha256sum --check --status && \
    chmod +x /opt/kubernetes/bin/skaffold

RUN curl -sL -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v3.8.1/kustomize_v3.8.1_linux_amd64.tar.gz && \
    echo "9d5b68f881ba89146678a0399469db24670cba4813e0299b47cb39a240006f37 /tmp/kustomize.tar.gz" | sha256sum --check --status && \
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize && \
    rm /tmp/kustomize.tar.gz

ENV PATH=/opt/kubernetes/bin:$PATH
