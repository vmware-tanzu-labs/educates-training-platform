#syntax=docker/dockerfile:1.3-labs

FROM kubernetesui/dashboard:v2.7.0 AS k8s-console

FROM fedora:36 AS system-base

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
        nc \
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
    echo "# set enable-bracketed-paste off" >> /etc/inputrc && \
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

RUN curl --silent --fail -L -o /tmp/dive.tar.gz https://github.com/wagoodman/dive/archive/refs/tags/v0.10.0.tar.gz && \
    echo "293e3ae853c8e7f77e4891addb4504a057ed3b6d97934cc97201031bcaa30b53 /tmp/dive.tar.gz" | sha256sum --check --status && \
    tar xvf /tmp/dive.tar.gz && \
    cd dive-0.10.0 && \
    go mod download && \
    go build -o main main.go

FROM system-base AS scratch-image

ARG TARGETARCH

# Kubernetes web console.

COPY --from=k8s-console / /opt/console/

# Miscellaneous tools.

RUN <<EOF
    set -eo pipefail
    VERSION=1.2.5
    CHECKSUM_amd64="0a8338f93a2cfa7686c0c5836f6ab7ad65275e483fbf517df46df4d306682cc2"
    CHECKSUM_arm64="44b963028d49075fbf9ea24926a2316dfb9a58603d3b8d3ece30cf1ac25f0088"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /usr/local/bin/bombardier https://github.com/codesenberg/bombardier/releases/download/v${VERSION}/bombardier-linux-${TARGETARCH}
    echo "${!CHECKSUM}  /usr/local/bin/bombardier" | sha256sum --check --status
    chmod +x /usr/local/bin/bombardier
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=4.33.3
    CHECKSUM_amd64="4ee662847c588c3ef2fec8bfb304e8739e3dbaba87ccb9a608d691c88f5b64dc"
    CHECKSUM_arm64="15925a972d268bcb0a7aa2236c7e5925b7a3ba4b5569bb57e943db7e8c6f834f"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v${VERSION}/yq_linux_${TARGETARCH}
    echo "${!CHECKSUM} /usr/local/bin/yq" | sha256sum --check --status
    chmod +x /usr/local/bin/yq
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.112.7
    CHECKSUM_amd64="d7ce8da76a9ba9b724981ced27a1a5a302041df7e22dbf84bf963f3c922a45ac"
    CHECKSUM_arm64="9dedb63589e1177fa6375cbe0becfdaba594a8fb7a7f40556a1c9c0a71ca1308"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/hugo.tar.gz https://github.com/gohugoio/hugo/releases/download/v${VERSION}/hugo_${VERSION}_linux-${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/hugo.tar.gz" | sha256sum --check --status
    cd /usr/local/bin
    tar -zxf /tmp/hugo.tar.gz hugo
    rm /tmp/hugo.tar.gz
EOF

COPY --from=builder-image /app/dive-0.10.0/main /usr/local/bin/dive

# Kubernetes tools.

RUN mkdir -p /opt/kubernetes/bin

RUN <<EOF
    set -eo pipefail
    VERSION=1.23.17
    CHECKSUM_amd64="f09f7338b5a677f17a9443796c648d2b80feaec9d6a094ab79a77c8a01fde941"
    CHECKSUM_arm64="c4a48fdc6038beacbc5de3e4cf6c23639b643e76656aabe2b7798d3898ec7f05"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.23 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.23" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.23
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.24.13
    CHECKSUM_amd64="52455fe485fa11c650ab07fea2e4856b5ea5a3e6ef8a1b3b6121e6361437fff9"
    CHECKSUM_arm64="750a2ee55b835994cda5f262bfa18debdcdb0d7a450875dca4f83c7cfffda353"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.24 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.24" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.24
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.25.9
    CHECKSUM_amd64="aaa5ea3b3630730d2b8a8ef3cccb14b47754602c7207c7b0717158ae83c7cb10"
    CHECKSUM_arm64="741e65b681a22074aaf9459b57dbcef6a9e993472b3019a87f57c191bc68575f"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.25 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.25" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.25
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.26.4
    CHECKSUM_amd64="636ac0eaa467dbceda4b2c4e33662adc9709f5ce40341c9fc1a687fc276ac02d"
    CHECKSUM_arm64="eea4054825a4c20cc09bc15abcb1354725ad886338e6892141a071caab91d4b6"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.26 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.26" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.26
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.27.1
    CHECKSUM_amd64="7fe3a762d926fb068bae32c399880e946e8caf3d903078bea9b169dcd5c17f6d"
    CHECKSUM_arm64="fd3cb8f16e6ed8aee9955b76e3027ac423b6d1cc7356867310d128082e2db916"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.27 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.27" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.27
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.26.7
    ARCHNAME_amd64=x86_64
    ARCHNAME_arm64=arm64
    ARCHNAME=ARCHNAME_${TARGETARCH}
    CHECKSUM_amd64="f774bb75045e361e17a4f267491c5ec66f41db7bffd996859ffb1465420af249"
    CHECKSUM_arm64="2888feae5298517cf4862251a8877ff978b3eb234cbc3ebc0d9eb07fc671673d"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/k9s.tar.gz https://github.com/derailed/k9s/releases/download/v${VERSION}/k9s_Linux_${!ARCHNAME}.tar.gz
    echo "${!CHECKSUM} /tmp/k9s.tar.gz" | sha256sum --check --status
    tar -C /tmp -zxf /tmp/k9s.tar.gz k9s
    mv /tmp/k9s /opt/kubernetes/bin/k9s
    rm /tmp/k9s.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.45.0
    CHECKSUM_amd64="d05f430ac18b3791d831f4cfd78371a7549f225dfaeb6fef2e5bfcd293d6c382"
    CHECKSUM_arm64="54e228823e851320b848d854218004299d2ff362e0fe9e287d5a52df502baaaf"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/ytt https://github.com/carvel-dev/ytt/releases/download/v${VERSION}/ytt-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/ytt" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/ytt
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.36.1
    CHECKSUM_amd64="194655166ca74d898c1225b42c9257cd0cb71128da271f233b8f12ceda7c15cc"
    CHECKSUM_arm64="9422215c35ab7ee7e6f53196679b6cd3c1c0873456082b00c72efdb7e263bc27"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/imgpkg https://github.com/carvel-dev/imgpkg/releases/download/v${VERSION}/imgpkg-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/imgpkg" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/imgpkg
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.37.0
    CHECKSUM_amd64="9f387e18043c95c922efbf879fc1d4d616b20c1c47aeae4f834c6f0069906735"
    CHECKSUM_arm64="0ffa023c69355ca43ae131be065963e30d576963a066e903c7691fb54a79d08c"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kbld https://github.com/carvel-dev/kbld/releases/download/v${VERSION}/kbld-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kbld" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kbld
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.55.0
    CHECKSUM_amd64="9aaa735985efbe240af0ca1d80adf3b43be6cf4ec6620a053082e31bea25dae7"
    CHECKSUM_arm64="944fdfebfdf1026d318609cc706bad454196f0b1d76e557b56c829b0e6165a9f"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kapp https://github.com/carvel-dev/kapp/releases/download/v${VERSION}/kapp-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kapp" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kapp
EOF

# RUN <<EOF
#     set -eo pipefail
#     VERSION=0.0.6
#     CHECKSUM_amd64="92a1f18be6a8dca15b7537f4cc666713b556630c20c9246b335931a9379196a0"
#     CHECKSUM_arm64="unavailable"
#     CHECKSUM=CHECKSUM_${TARGETARCH}
#     curl --silent --fail -L -o /opt/kubernetes/bin/kwt https://github.com/carvel-dev/kwt/releases/download/v${VERSION}/kwt-linux-${TARGETARCH}
#     echo "${!CHECKSUM} /opt/kubernetes/bin/kwt" | sha256sum --check --status
#     chmod +x /opt/kubernetes/bin/kwt
# EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.33.1
    CHECKSUM_amd64="6c9ed811fe9983e03424f2ecfc00a4aaeb19646ef27c42eb2a6c643ea07bd32b"
    CHECKSUM_arm64="79e026faaa1ac75c36414a97ee7e58b4bf9c148b1ce34aee795c667b71745519"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/vendir https://github.com/carvel-dev/vendir/releases/download/v${VERSION}/vendir-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/vendir" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/vendir
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.45.0
    CHECKSUM_amd64="1841b8684fcee57d4707094092bbc21a88f60293a9a77605fea9cfe10f1d95c7"
    CHECKSUM_arm64="434093ea3bc802b1ad37a5f96ffde3669eec0f57ffc4f1279cc3fa9d07106527"
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
    VERSION=3.11.3
    CHECKSUM_amd64="ca2d5d40d4cdfb9a3a6205dd803b5bc8def00bd2f13e5526c127e9b667974a89"
    CHECKSUM_arm64="9f58e707dcbe9a3b7885c4e24ef57edfb9794490d72705b33a93fa1f3572cce4"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/helm.tar.gz https://get.helm.sh/helm-v${VERSION}-linux-${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/helm.tar.gz" | sha256sum --check --status
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-${TARGETARCH}/helm
    rm /tmp/helm.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=2.3.1
    CHECKSUM_amd64="dd252b19a762a1cd9929f9ce0a55ae43877004b1c80e119324a66ffb093ee8c6"
    CHECKSUM_arm64="88e8107bfcbee7ab2738211e265ca27bfee4b2562bc29b2a6f11a53b08789876"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v${VERSION}/skaffold-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/skaffold" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/skaffold
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=5.0.1
    CHECKSUM_amd64="dca623b36aef84fbdf28f79d02e9b3705ff641424ac1f872d5420dadb12fb78d"
    CHECKSUM_arm64="c6e036c5c7eee4c15f7544e441ced5cb6cf9eba24a011c25008df5617cd2fb85"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v${VERSION}/kustomize_v${VERSION}_linux_${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/kustomize.tar.gz" | sha256sum --check --status
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize
    rm /tmp/kustomize.tar.gz
EOF

# VS Code editor and dashboard extension.

RUN <<EOF
    set -eo pipefail
    VERSION=4.12.0
    CHECKSUM_amd64="d50ee947c4144a6ff2656e664ecbb3f70b75168b8a6e8c3eef47787f3c240c26"
    CHECKSUM_arm64="2cddd82a010f61a4bd20d6cc3c50e924b01a83e938e5e4e882e36a541208f7c8"
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
    mkdir -p /opt/slides/reveal.js/4.5.0 && \
    cd /opt/slides/reveal.js/4.5.0 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/4.5.0.tar.gz && \
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
