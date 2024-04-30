#syntax=docker/dockerfile:1.3-labs

FROM kubernetesui/dashboard:v2.7.0 AS k8s-console

FROM fedora:39 AS system-base

RUN HOME=/root && \
    INSTALL_PKGS=" \
        bash-completion \
        buildah \
        cadaver \
        containerd.io \
        docker-ce \
        docker-ce-cli \
        docker-compose-plugin \
        findutils \
        fuse3 \
        gcc \
        gcc-c++ \
        gettext \
        git \
        glibc-langpack-en \
        httpd \
        httpd-devel \
        httpie \
        jq \
        less \
        make \
        nano \
        ncat \
        netcat \
        nodejs \
        openssh-server \
        perl-Digest-SHA \
        procps \
        python3 \
        python3-devel \
        python3-pip \
        python3-virtualenv \
        python3-wheel \
        redhat-rpm-config \
        siege \
        slirp4netns \
        skopeo \
        supervisor \
        sudo \
        tree \
        tmux \
        vim-enhanced \
        which \
        yarn \
        zlib-devel \
    " && \
    dnf install -y dnf-plugins-core && \
    dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo && \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1 && \
    dnf install https://rpm.nodesource.com/pub_16.x/nodistro/repo/nodesource-release-nodistro-1.noarch.rpm -y && \
    curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo && \
    dnf install -y --setopt=tsflags=nodocs --setopt=nodesource-nodejs.module_hotfixes=1 $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all && \
    sed -i.bak -e '1i auth requisite pam_deny.so' /etc/pam.d/su && \
    sed -i.bak -e 's/^%wheel/# %wheel/' /etc/sudoers && \
    useradd -u 1001 -g 0 -M -d /home/eduk8s eduk8s && \
    mkdir -p /home/eduk8s && \
    chown -R 1001:0 /home/eduk8s && \
    chmod -R g=u /home/eduk8s && \
    chmod g+w /etc/passwd && \
    chown 1001:0 /opt && \
    ln -s /var/run/docker/docker.sock /var/run/docker.sock

FROM system-base AS vscode-helper

COPY opt/helper /opt/helper

WORKDIR /opt/helper

RUN npm install && \
    npm run vsce-package

FROM golang:1.19-buster as builder-image

WORKDIR /app

RUN curl --silent --fail -L -o /tmp/git-serve.tar.gz https://github.com/cirocosta/git-serve/archive/refs/tags/v0.0.5.tar.gz && \
echo "09cd14a34f17d88cd4f0d2b73e0bbd0bf56984be21bc947f416a7824a709011e /tmp/git-serve.tar.gz" | sha256sum --check --status && \
    tar xvf /tmp/git-serve.tar.gz && \
    cd git-serve-0.0.5 && \
    go mod download && \
    go build -o git-serve cmd/git-serve/main.go

RUN curl --silent --fail -L -o /tmp/dive.tar.gz https://github.com/wagoodman/dive/archive/refs/tags/v0.11.0.tar.gz && \
    echo "e91d3ce4b2dd292a72effea9c7dbde0f92a05f29a4e4c89fd46ed1d7f6aaed97 /tmp/dive.tar.gz" | sha256sum --check --status && \
    tar xvf /tmp/dive.tar.gz && \
    cd dive-0.11.0 && \
    go mod download && \
    go build -o main main.go

FROM system-base AS scratch-image

ARG TARGETARCH

# Kubernetes web console.

COPY --from=k8s-console / /opt/console/

# Miscellaneous tools.

RUN <<EOF
    set -eo pipefail
    VERSION=1.2.6
    CHECKSUM_amd64="c29be68fb6711434d50d8c25bc5ce08d33d8265871e6e1a518b3775e530fbb9b"
    CHECKSUM_arm64="3064a2c7639b8f4c682895cbd8f7791c272200066d68837591e3204988cd6190"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /usr/local/bin/bombardier https://github.com/codesenberg/bombardier/releases/download/v${VERSION}/bombardier-linux-${TARGETARCH}
    echo "${!CHECKSUM}  /usr/local/bin/bombardier" | sha256sum --check --status
    chmod +x /usr/local/bin/bombardier
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=4.40.5
    CHECKSUM_amd64="0d6aaf1cf44a8d18fbc7ed0ef14f735a8df8d2e314c4cc0f0242d35c0a440c95"
    CHECKSUM_arm64="9431f0fa39a0af03a152d7fe19a86e42e9ff28d503ed4a70598f9261ec944a97"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v${VERSION}/yq_linux_${TARGETARCH}
    echo "${!CHECKSUM} /usr/local/bin/yq" | sha256sum --check --status
    chmod +x /usr/local/bin/yq
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.121.1
    CHECKSUM_amd64="348997284f405abee2a84634525a4e1298b710bbf5bdf5dea30bfc0b1c9aeba5"
    CHECKSUM_arm64="60973296797730b13febc491db3f966f227d8e4d1ff244bdfbb323923abef0c7"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/hugo.tar.gz https://github.com/gohugoio/hugo/releases/download/v${VERSION}/hugo_${VERSION}_linux-${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/hugo.tar.gz" | sha256sum --check --status
    cd /usr/local/bin
    tar -zxf /tmp/hugo.tar.gz hugo
    rm /tmp/hugo.tar.gz
EOF

COPY --from=builder-image /app/dive-0.11.0/main /usr/local/bin/dive

# Kubernetes tools.

RUN mkdir -p /opt/kubernetes/bin

RUN <<EOF
    set -eo pipefail
    VERSION=1.24.17
    CHECKSUM_amd64="3e9588e3326c7110a163103fc3ea101bb0e85f4d6fd228cf928fa9a2a20594d5"
    CHECKSUM_arm64="66885bda3a202546778c77f0b66dcf7f576b5a49ff9456acf61329da784a602d"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.24 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.24" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.24
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.25.16
    CHECKSUM_amd64="5a9bc1d3ebfc7f6f812042d5f97b82730f2bdda47634b67bddf36ed23819ab17"
    CHECKSUM_arm64="d6c23c80828092f028476743638a091f2f5e8141273d5228bf06c6671ef46924"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.25 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.25" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.25
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.26.11
    CHECKSUM_amd64="27c34a0870230d9dd723e1e01114634e396cd2a3d25ced263b769a4bd53e4edd"
    CHECKSUM_arm64="4a6d2b7204af3cf84cd0e2c670fbb211501050c9a288de49de3c6363d4e0a63e"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.26 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.26" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.26
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.27.8
    CHECKSUM_amd64="027b3161e99fa0a7fa529e8f17f73ee2c0807c81c721ca7cf307f6b41c17bc57"
    CHECKSUM_arm64="97ed6739e2803e63fd2d9de78be22d5ba6205bb63179a16ec773063526525a8e"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.27 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.27" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.27
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.28.4
    CHECKSUM_amd64="893c92053adea6edbbd4e959c871f5c21edce416988f968bec565d115383f7b8"
    CHECKSUM_arm64="edf1e17b41891ec15d59dd3cc62bcd2cdce4b0fd9c2ee058b0967b17534457d7"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.28 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.28" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.28
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.29.1
    CHECKSUM_amd64="b7ed81a8952a5520a1a6978c3cf68b1fd555d928a444c63d4b826ae6fbb6d9ff"
    CHECKSUM_arm64="f9dbd1ff1cd26d851c8ac695decbc4ceea97f2a87ccfa16ff805ab5f49ae9b81"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v${VERSION}/k9s_Linux_${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/k9s.tar.gz" | sha256sum --check --status
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s
    mv /tmp/k9s /opt/kubernetes/bin/k9s
    rm /tmp/k9s.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.46.3
    CHECKSUM_amd64="2b4ca5365c343bb1e903e8e845d9750b5d2776b3a99483912f27da6e95c480c0"
    CHECKSUM_arm64="5372597c7165cb09657c7b9cfb5da1e58673940cf0ebbd4ecf8040e9ab9eb9e7"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/ytt https://github.com/carvel-dev/ytt/releases/download/v${VERSION}/ytt-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/ytt" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/ytt
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.39.0
    CHECKSUM_amd64="98b80baa5d665c5119fc8e2a62978f9d193c9647e3c47ab72867b055b94d14ff"
    CHECKSUM_arm64="7b247c24850dbf4ff70095b6d7f5aff12aea15d0ece9e9ecf66f92e3c9d2f332"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/imgpkg https://github.com/carvel-dev/imgpkg/releases/download/v${VERSION}/imgpkg-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/imgpkg" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/imgpkg
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.38.2
    CHECKSUM_amd64="bd471a1270481f04a3ad656b5911167cd4173ff7c1cc524ddc27569b02978a74"
    CHECKSUM_arm64="36bb1e689247aca092c9cff7b349adb505760c257ccf1fcdf25a54086182c37c"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kbld https://github.com/carvel-dev/kbld/releases/download/v${VERSION}/kbld-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kbld" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kbld
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.59.2
    CHECKSUM_amd64="6986369c06e89bcec366b2cc18f81634fcd95e2b52c6c6f7ee46b497ade25f7d"
    CHECKSUM_arm64="03d8ef43aa467756a22fea6d32745b3bddef163fa22de4f8b5edd1d60fdc0585"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kapp https://github.com/carvel-dev/kapp/releases/download/v${VERSION}/kapp-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kapp" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kapp
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.0.8
    CHECKSUM_amd64="1022483a8b59fe238e782a9138f1fee6ca61ecf7ccd1e5f0d98e95c56df94d87"
    CHECKSUM_arm64="7b94a134cbde5ff2e245d102f54b9ac9f81b3fcc5e54a5cefecc1e5845b8a65f"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kwt https://github.com/carvel-dev/kwt/releases/download/v${VERSION}/kwt-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kwt" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kwt
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.38.0
    CHECKSUM_amd64="49076dd93ae931ac0d341d81e51b6fdb2288c718cfda8279b78e31c6d389da5f"
    CHECKSUM_arm64="88e3588632f58f44f31d3fa19f60d4aad8ea0075b6fc68956a9d061d8de2442d"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/vendir https://github.com/carvel-dev/vendir/releases/download/v${VERSION}/vendir-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/vendir" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/vendir
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.49.0
    CHECKSUM_amd64="ed47847850039cf5572af49420d0365b2cc68a3a731fbc5e8a23b13eb8ffb020"
    CHECKSUM_arm64="f513b6b58a75b45506c3a347f63118bd4abffab9c69975c32089c7756d5807a4"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kctrl https://github.com/carvel-dev/kapp-controller/releases/download/v${VERSION}/kctrl-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kctrl" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kctrl
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.12.1
    ARCHNAME_amd64=64bit
    ARCHNAME_arm64=arm64
    ARCHNAME=ARCHNAME_${TARGETARCH}
    CHECKSUM_amd64="b56ca09fb92314eb6a7b1a0ddcc65b582990e3fdef6e2a996cacd4a24b4e54bf"
    CHECKSUM_arm64="2808448a78d7c55e40ed34bcd3cd4db04b5cf847884938af047b73eb7a40bcd5"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v${VERSION}/octant_${VERSION}_Linux-${!ARCHNAME}.tar.gz
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_${VERSION}_Linux-${!ARCHNAME}/octant
    mv /opt/kubernetes/bin/octant /opt/kubernetes/bin/octant@${VERSION}
    rm -f /tmp/octant.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.25.1
    ARCHNAME_amd64=64bit
    ARCHNAME_arm64=arm64
    ARCHNAME=ARCHNAME_${TARGETARCH}
    CHECKSUM_amd64="b12bb6752e43f4e0fe54278df8e98dee3439c4066f66cdb7a0ca4a1c7d8eaa1e"
    CHECKSUM_arm64="a3eb4973a0c869267e3916bd43e0b41b2bbc73b898376b795a617299c7b2a623"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/octant.tar.gz https://github.com/vmware-tanzu/octant/releases/download/v${VERSION}/octant_${VERSION}_Linux-${!ARCHNAME}.tar.gz
    tar -C /opt/kubernetes/bin --strip-components 1 -xf /tmp/octant.tar.gz octant_${VERSION}_Linux-${!ARCHNAME}/octant
    mv /opt/kubernetes/bin/octant /opt/kubernetes/bin/octant@${VERSION}
    ln -s octant@${VERSION} /opt/kubernetes/bin/octant@latest
    rm -f /tmp/octant.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=3.13.3
    CHECKSUM_amd64="bbb6e7c6201458b235f335280f35493950dcd856825ddcfd1d3b40ae757d5c7d"
    CHECKSUM_arm64="44aaa094ae24d01e8c36e327e1837fd3377a0f9152626da088384c5bc6d94562"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/helm.tar.gz https://get.helm.sh/helm-v${VERSION}-linux-${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/helm.tar.gz" | sha256sum --check --status
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-${TARGETARCH}/helm
    rm /tmp/helm.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=2.9.0
    CHECKSUM_amd64="7eed2d7fe4c1a53f385d0b24c50fc08941a09ac37b44705ad7997a6635c27e84"
    CHECKSUM_arm64="2655f412582c1b0e84f6822c273b8d8d14df427598fd760a6311ed1280942051"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v${VERSION}/skaffold-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/skaffold" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/skaffold
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=5.3.0
    CHECKSUM_amd64="3ab32f92360d752a2a53e56be073b649abc1e7351b912c0fb32b960d1def854c"
    CHECKSUM_arm64="a1ec622d4adeb483e3cdabd70f0d66058b1e4bcec013c4f74f370666e1e045d8"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v${VERSION}/kustomize_v${VERSION}_linux_${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/kustomize.tar.gz" | sha256sum --check --status
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize
    rm /tmp/kustomize.tar.gz
EOF

# VS Code editor and dashboard extension.

RUN <<EOF
    set -eo pipefail
    VERSION=4.19.1
    CHECKSUM_amd64="792a2ebc2a3a8577579924aea149dc104feb20b13b98c4a34914f9a634123278"
    CHECKSUM_arm64="084098d0de5d166cca1e9587dffedf39222b6b16933ad6258a256137f5ef14f0"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    mkdir /opt/editor
    curl --silent --fail -L -o /tmp/code-server.tar.gz https://github.com/cdr/code-server/releases/download/v${VERSION}/code-server-${VERSION}-linux-${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/code-server.tar.gz" | sha256sum --check --status
    cd /opt/editor
    tar -zxf /tmp/code-server.tar.gz --strip-components=1
    rm /tmp/code-server.tar.gz
EOF

COPY --from=vscode-helper --chown=1001:0 /opt/helper/educates-0.0.1.vsix /opt/eduk8s/educates-0.0.1.vsix

# Git server.

RUN mkdir /opt/git /opt/git/bin /opt/git/repositories

COPY --from=builder-image /app/git-serve-0.0.5/git-serve /opt/git/bin/git-serve

# Dashboard applications.

COPY opt/. /opt/

RUN mkdir -p /opt/slides/reveal.js/3.9.2 && \
    cd /opt/slides/reveal.js/3.9.2 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/3.9.2.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/reveal.js/4.6.0 && \
    cd /opt/slides/reveal.js/4.6.0 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/4.6.0.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/reveal.js/5.0.3 && \
    cd /opt/slides/reveal.js/5.0.3 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/5.0.3.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/impress.js/1.1.0 && \
    cd /opt/slides/impress.js/1.1.0 && \
    curl -sL -o src.tar.gz https://github.com/impress/impress.js/archive/refs/tags/1.1.0.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/impress.js/2.0.0 && \
    cd /opt/slides/impress.js/2.0.0 && \
    curl -sL -o src.tar.gz https://github.com/impress/impress.js/archive/refs/tags/v2.0.0.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz

RUN cd /opt/httpd && \
    virtualenv /opt/httpd && \
    source /opt/httpd/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

RUN cd /opt/gateway && \
    npm install && \
    npm run compile && \
    npm prune --production && \
    npm cache clean --force

RUN cd /opt/renderer && \
    npm install && \
    npm run compile && \
    npm prune --production && \
    npm cache clean --force

FROM system-base

ARG TARGETARCH

COPY --from=scratch-image --chown=1001:0 /opt/. /opt/
COPY --from=scratch-image --chown=1001:0 /home/. /home/

COPY --from=scratch-image /usr/local/. /usr/local/

COPY usr/. /usr/
COPY etc/. /etc/

COPY --chown=1001:0 home/. /home/

RUN rm /etc/supervisord.conf && \
    ln -s /opt/eduk8s/etc/supervisord.conf /etc/supervisord.conf

RUN fix-permissions /home/eduk8s

ENV HOME=/home/eduk8s \
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/kubernetes/bin:/opt/editor/bin:$PATH \
    PLATFORM_ARCH=${TARGETARCH}

ENV BASH_ENV=/opt/eduk8s/etc/profile \
    ENV=/opt/eduk8s/etc/profile \
    PROMPT_COMMAND=". /opt/eduk8s/etc/profile"

WORKDIR /home/eduk8s

USER 1001

ENTRYPOINT [ "container-entrypoint" ]

EXPOSE 10081

CMD [ "start-container" ]
