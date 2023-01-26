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
        jq \
        less \
        make \
        nano \
        nc \
        nodejs \
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
    curl -sL https://rpm.nodesource.com/setup_14.x | bash - && \
    curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all && \
    sed -i.bak -e '1i auth requisite pam_deny.so' /etc/pam.d/su && \
    sed -i.bak -e 's/^%wheel/# %wheel/' /etc/sudoers && \
    echo "set enable-bracketed-paste off" >> /etc/inputrc && \
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
    VERSION=4.30.8
    CHECKSUM_amd64="6c911103e0dcc54e2ba07e767d2d62bcfc77452b39ebaee45b1c46f062f4fd26"
    CHECKSUM_arm64="95092e8b5332890c46689679b5e4360d96873c025ad8bafd961688f28ea434c7"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v${VERSION}/yq_linux_${TARGETARCH}
    echo "${!CHECKSUM} /usr/local/bin/yq" | sha256sum --check --status
    chmod +x /usr/local/bin/yq
EOF

COPY --from=builder-image /app/dive-0.10.0/main /usr/local/bin/dive

# Kubernetes tools.

RUN mkdir -p /opt/kubernetes/bin

RUN <<EOF
    set -eo pipefail
    VERSION=1.20.15
    CHECKSUM_amd64="d283552d3ef3b0fd47c08953414e1e73897a1b3f88c8a520bb2e7de4e37e96f3"
    CHECKSUM_arm64="d479febfb2e967bd86240b5c0b841e40e39e1ef610afd6f224281a23318c13dc"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.20 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.20" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.20
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.21.14
    CHECKSUM_amd64="0c1682493c2abd7bc5fe4ddcdb0b6e5d417aa7e067994ffeca964163a988c6ee"
    CHECKSUM_arm64="a23151bca5d918e9238546e7af416422b51cda597a22abaae5ca50369abfbbaa"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.21 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.21" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.21
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.21.14
    CHECKSUM_amd64="0c1682493c2abd7bc5fe4ddcdb0b6e5d417aa7e067994ffeca964163a988c6ee"
    CHECKSUM_arm64="a23151bca5d918e9238546e7af416422b51cda597a22abaae5ca50369abfbbaa"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.21 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.21" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.21
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.22.17
    CHECKSUM_amd64="7506a0ae7a59b35089853e1da2b0b9ac0258c5309ea3d165c3412904a9051d48"
    CHECKSUM_arm64="8fc2f8d5c80a6bf60be06f8cf28679a05ce565ce0bc81e70aaac38e0f7da6259"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.22 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.22" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.22
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.23.16
    CHECKSUM_amd64="5f914edc9dbfbe1b8b8dc0f5dbbac28720a8dffeb940e3339c371e3612c37e48"
    CHECKSUM_arm64="a304cb4d5815e05a45f00ac9fccfae32761a5a3e26cae40c2791b28b0b80db2d"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.23 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.23" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.23
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.24.10
    CHECKSUM_amd64="d8e9cd9bb073ff09e2f2a74cf48e94a9b9d4f2fa2e2dd91b68b01f64e7061a3b"
    CHECKSUM_arm64="3a0fa419264b3df077bc8220d721d6cbef6cc944014d9337adfd4434ac23bebf"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.24 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.24" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.24
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=1.25.6
    CHECKSUM_amd64="ba876aef0e9d7e2e8fedac036ec194de5ec9b6d2953e30ff82a2758c6ba32174"
    CHECKSUM_arm64="1a4e2850e94d44039c73eae7a6e005b3e1435c00a62bd58df7643bdeb8475cfd"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kubectl@1.25 https://storage.googleapis.com/kubernetes-release/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl
    echo "${!CHECKSUM} /opt/kubernetes/bin/kubectl@1.25" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kubectl@1.25
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
    VERSION=0.44.1
    CHECKSUM_amd64="9f2f151cf42a54cdfee5ee1a98b7255821c9c047498d4af788cec8c4cf520fb8"
    CHECKSUM_arm64="2b29dfb97be4a7333ab1e911887c884b2d1de16ee75f16b697fdbfe9661f58be"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/ytt https://github.com/carvel-dev/ytt/releases/download/v${VERSION}/ytt-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/ytt" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/ytt
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.35.0
    CHECKSUM_amd64="2c289cf6b5c88a4dd4bec17c9e57e49c2c7531c127ea130737945392cdc65362"
    CHECKSUM_arm64="eb972061a7a71b03ee224b3e3d7aa0ec9a45ec20a6c8c5b11917b223c58a9570"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/imgpkg https://github.com/carvel-dev/imgpkg/releases/download/v${VERSION}/imgpkg-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/imgpkg" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/imgpkg
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.35.0
    CHECKSUM_amd64="2c289cf6b5c88a4dd4bec17c9e57e49c2c7531c127ea130737945392cdc65362"
    CHECKSUM_arm64="eb972061a7a71b03ee224b3e3d7aa0ec9a45ec20a6c8c5b11917b223c58a9570"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/imgpkg https://github.com/carvel-dev/imgpkg/releases/download/v${VERSION}/imgpkg-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/imgpkg" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/imgpkg
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.36.1
    CHECKSUM_amd64="fa954cf4e288d61e671a2be93d41d08309951d705b1f02d4c90213aa5736add5"
    CHECKSUM_arm64="b457413588f5911fd3dc04f1143fd683e322228090cb3024c0d58463ce6f0a4e"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/kbld https://github.com/carvel-dev/kbld/releases/download/v${VERSION}/kbld-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/kbld" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/kbld
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.54.1
    CHECKSUM_amd64="436e30a34647b2d889010d08a9242b4d3954f4c84c9ca26dd30751934ecf9950"
    CHECKSUM_arm64="197971e92b44a54ddeb28aa3549310382c1a109e408a485b6eb41d9d0b73dba3"
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
    VERSION=0.30.1
    CHECKSUM_amd64="ab660041eb5144521425ad4c1703bcd62acf32a64401e2a3200ebb91358b65c4"
    CHECKSUM_arm64="162a1d188f9881d34e052bde56fed89d483d4b7584e7234dfc90bffa92a1f63b"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/vendir https://github.com/carvel-dev/vendir/releases/download/v${VERSION}/vendir-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/vendir" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/vendir
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=0.44.1
    CHECKSUM_amd64="7b333bdffc69b21c85b0d7695d6932a2e1da96684546259aa77e272bfab1cbab"
    CHECKSUM_arm64="d1705d862f1af0ecf54facc2e39300e8f979eb276d8902b42170a76266b04512"
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
    VERSION=3.11.0
    CHECKSUM_amd64="6c3440d829a56071a4386dd3ce6254eab113bc9b1fe924a6ee99f7ff869b9e0b"
    CHECKSUM_arm64="57d36ff801ce8c0201ce9917c5a2d3b4da33e5d4ea154320962c7d6fb13e1f2c"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/helm.tar.gz https://get.helm.sh/helm-v${VERSION}-linux-${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/helm.tar.gz" | sha256sum --check --status
    tar -C /opt/kubernetes/bin --strip-components 1 -zxvf /tmp/helm.tar.gz linux-${TARGETARCH}/helm
    rm /tmp/helm.tar.gz
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=2.1.0
    CHECKSUM_amd64="62fe1c68bf8b177e43fb900a4166b4f087ac5b68f927a6854d625bf38c8bcc41"
    CHECKSUM_arm64="31843ba1ea91d8fe62bdbc07e6c67fe57e1d2f847862305b89ffe34905fda2ec"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /opt/kubernetes/bin/skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v${VERSION}/skaffold-linux-${TARGETARCH}
    echo "${!CHECKSUM} /opt/kubernetes/bin/skaffold" | sha256sum --check --status
    chmod +x /opt/kubernetes/bin/skaffold
EOF

RUN <<EOF
    set -eo pipefail
    VERSION=4.5.7
    CHECKSUM_amd64="701e3c4bfa14e4c520d481fdf7131f902531bfc002cb5062dcf31263a09c70c9"
    CHECKSUM_arm64="65665b39297cc73c13918f05bbe8450d17556f0acd16242a339271e14861df67"
    CHECKSUM=CHECKSUM_${TARGETARCH}
    curl --silent --fail -L -o /tmp/kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v${VERSION}/kustomize_v${VERSION}_linux_${TARGETARCH}.tar.gz
    echo "${!CHECKSUM} /tmp/kustomize.tar.gz" | sha256sum --check --status
    tar -C /opt/kubernetes/bin -zxvf /tmp/kustomize.tar.gz kustomize
    rm /tmp/kustomize.tar.gz
EOF

# VS Code editor and dashboard extension.

RUN <<EOF
    set -eo pipefail
    VERSION=4.9.1
    CHECKSUM_amd64="3ea79c9dc03544ea06abe7da660c1bc0e4376337070211d98ffa8c33889cd57e"
    CHECKSUM_arm64="6e9fedb726eb13b5ef60a77bf16a1ee9911684b7e211e90eee7a0e9e82bac9e4"
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
    mkdir -p /opt/slides/reveal.js/4.3.1 && \
    cd /opt/slides/reveal.js/4.3.1 && \
    curl -sL -o src.tar.gz https://github.com/hakimel/reveal.js/archive/4.3.1.tar.gz && \
    tar --strip-components 1 -xf src.tar.gz && \
    rm src.tar.gz && \
    mkdir -p /opt/slides/impress.js/1.1.0 && \
    cd /opt/slides/impress.js/1.1.0 && \
    curl -sL -o src.tar.gz https://github.com/impress/impress.js/archive/refs/tags/1.1.0.tar.gz && \
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
    PATH=/home/eduk8s/bin:/opt/eduk8s/bin:/opt/kubernetes/bin:/opt/editor/bin:$PATH

ENV REGISTRY_AUTH_FILE=/home/eduk8s/.docker/config.json

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

ENV BASH_ENV=/opt/eduk8s/etc/profile \
    ENV=/opt/eduk8s/etc/profile \
    PROMPT_COMMAND=". /opt/eduk8s/etc/profile"

WORKDIR /home/eduk8s

USER 1001

ENTRYPOINT [ "container-entrypoint" ]

EXPOSE 10081

CMD [ "start-container" ]
