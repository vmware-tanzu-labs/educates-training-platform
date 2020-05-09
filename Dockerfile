FROM fedora:31

COPY --chown=1001:0 opt/. /opt/

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.11 https://storage.googleapis.com/kubernetes-release/release/v1.11.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.11

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.12 https://storage.googleapis.com/kubernetes-release/release/v1.12.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.12

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.13 https://storage.googleapis.com/kubernetes-release/release/v1.13.12/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.13

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.14 https://storage.googleapis.com/kubernetes-release/release/v1.14.10/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.14

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.15 https://storage.googleapis.com/kubernetes-release/release/v1.15.12/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.15

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.16 https://storage.googleapis.com/kubernetes-release/release/v1.16.9/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.16

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.17 https://storage.googleapis.com/kubernetes-release/release/v1.17.5/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.17

RUN curl -sL -o /opt/kubernetes/bin/kubectl@1.18 https://storage.googleapis.com/kubernetes-release/release/v1.18.2/bin/linux/amd64/kubectl && \
    chmod +x /opt/kubernetes/bin/kubectl@1.18

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v3/clients/3.11.215/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@3.11 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.1/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.1 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.2/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.2 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.3/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.3 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.4/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.4 && \
    rm /tmp/oc.tar.gz

RUN curl -s -o /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v4/clients/oc/4.5/linux/oc.tar.gz && \
    tar -C /tmp -zxf /tmp/oc.tar.gz oc && \
    mv /tmp/oc /opt/kubernetes/bin/oc@4.5 && \
    rm /tmp/oc.tar.gz

RUN curl -sL -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.19.2/k9s_Linux_x86_64.tar.gz && \
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s && \
    mv /tmp/k9s /opt/kubernetes/bin/k9s && \
    rm /tmp/k9s.tar.gz

RUN curl -sL -o /opt/kubernetes/bin/ytt https://github.com/k14s/ytt/releases/download/v0.27.1/ytt-linux-amd64 && \
    echo "b53674a21d99576b8d69483113e1ec73d9a3ed7381170a421c9afcf8aa551f15 /opt/kubernetes/bin/ytt" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/ytt

RUN curl -sL -o /opt/kubernetes/bin/kapp https://github.com/k14s/kapp/releases/download/v0.24.0/kapp-linux-amd64 && \
    echo "044a8355c1a3aa4c9e427fc64f7074b80cb759e539771d70d38933886dbd2df4 /opt/kubernetes/bin/kapp" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kapp

RUN curl -sL -o /opt/kubernetes/bin/kbld https://github.com/k14s/kbld/releases/download/v0.20.0/kbld-linux-amd64 && \
    echo "a0e7dd4072587aa26db59a74bb2aadeee55ab5d285dd0544cb8eaff11821ed33 /opt/kubernetes/bin/kbld" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kbld

RUN curl -sL -o /opt/kubernetes/bin/kwt https://github.com/k14s/kwt/releases/download/v0.0.6/kwt-linux-amd64 && \
    echo "92a1f18be6a8dca15b7537f4cc666713b556630c20c9246b335931a9379196a0 /opt/kubernetes/bin/kwt" | sha256sum --check --status && \
    chmod 775 /opt/kubernetes/bin/kwt

RUN curl -sL -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v0.12.1/octant_0.12.1_Linux-64bit.tar.gz && \
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_0.12.1_Linux-64bit/octant && \
    rm -f /tmp/octant.tar.gz

ENV PATH=/opt/kubernetes/bin:$PATH
