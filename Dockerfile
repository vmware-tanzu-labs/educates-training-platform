FROM fedora:31 as java-base

USER root

RUN HOME=/root && \
    INSTALL_PKGS=" \
        unzip \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all && \
    sed -i.bak -e '1i auth requisite pam_deny.so' /etc/pam.d/su && \
    sed -i.bak -e 's/^%wheel/# %wheel/' /etc/sudoers && \
    useradd -u 1001 -g 0 -M -d /home/eduk8s eduk8s && \
    mkdir -p /home/eduk8s && \
    chown -R 1001:0 /home/eduk8s && \
    chmod -R g=u /home/eduk8s && \
    chmod g+w /etc/passwd && \
    chown 1001:0 /opt

USER 1001

RUN mkdir -p /opt/{jdk8,jdk11,gradle,maven}

RUN curl -sL -o /tmp/jdk8.tar.gz https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/jdk8u282-b08/OpenJDK8U-jdk_x64_linux_hotspot_8u282b08.tar.gz && \
    echo "e6e6e0356649b9696fa5082cfcb0663d4bef159fc22d406e3a012e71fce83a5c /tmp/jdk8.tar.gz" | sha256sum --check --status && \
    tar -C /opt/jdk8 --strip-components 1 -zxf /tmp/jdk8.tar.gz && \
    rm /tmp/jdk8.tar.gz

RUN curl -sL -o /tmp/jdk11.tar.gz https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.10%2B9/OpenJDK11U-jdk_x64_linux_hotspot_11.0.10_9.tar.gz && \
    echo "ae78aa45f84642545c01e8ef786dfd700d2226f8b12881c844d6a1f71789cb99 /tmp/jdk11.tar.gz" | sha256sum --check --status && \
    tar -C /opt/jdk11 --strip-components 1 -zxf /tmp/jdk11.tar.gz && \
    rm /tmp/jdk11.tar.gz

RUN curl -sL -o /tmp/maven.tar.gz http://www.us.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz && \
    echo "c35a1803a6e70a126e80b2b3ae33eed961f83ed74d18fcd16909b2d44d7dada3203f1ffe726c17ef8dcca2dcaa9fca676987befeadc9b9f759967a8cb77181c0 /tmp/maven.tar.gz" | sha512sum --check --status && \
    tar -C /opt/maven --strip-components 1 -zxf /tmp/maven.tar.gz && \
    rm /tmp/maven.tar.gz

RUN curl -sL -o /tmp/gradle.zip https://services.gradle.org/distributions/gradle-6.8.2-bin.zip && \
    echo "8de6efc274ab52332a9c820366dd5cf5fc9d35ec7078fd70c8ec6913431ee610 /tmp/gradle.zip" | sha256sum --check --status && \
    unzip -d /opt/gradle /tmp/gradle.zip && \
    mv /opt/gradle/gradle-6.8.2/* /opt/gradle/ && \
    rm -rf /opt/gradle/gradle-6.8.2 && \
    rm /tmp/gradle.zip

ENV PATH=/opt/jdk11/bin:/opt/gradle/bin:/opt/maven/bin:$PATH \
    JAVA_HOME=/opt/jdk11 \
    M2_HOME=/opt/maven

WORKDIR /home/eduk8s

FROM java-base as mvn-wrapper

RUN mvn -N io.takari:maven:0.7.7:wrapper && \
    /home/eduk8s/mvnw -v

FROM java-base as gradle-wrapper

RUN gradle wrapper --gradle-version=6.8.2 --distribution-type=bin

FROM quay.io/eduk8s/pkgs-code-server:210217.053122.50c1d76 AS code-server

RUN EXTENSIONS=" \
      pivotal.vscode-spring-boot@1.17.0 \
      redhat.java@0.61.0 \
      redhat.vscode-xml@0.12.0 \
      vscjava.vscode-java-debug@0.27.1 \
      vscjava.vscode-java-dependency@0.13.0 \
      vscjava.vscode-java-test@0.24.2 \
      vscjava.vscode-maven@0.21.2 \
      vscjava.vscode-spring-initializr@0.4.6 \
    " && \
    mkdir /opt/code-server/java-extensions && \
    for extension in $EXTENSIONS; do /opt/code-server/bin/code-server --extensions-dir /opt/code-server/java-extensions --install-extension $extension; done

FROM java-base

COPY --chown=1001:0 --from=mvn-wrapper /home/eduk8s/.m2 /home/eduk8s/.m2

COPY --chown=1001:0 --from=gradle-wrapper /home/eduk8s/.gradle /home/eduk8s/.gradle

COPY --chown=1001:0 --from=code-server /opt/code-server/java-extensions/. /opt/code-server/extensions/

COPY --chown=1001:0 opt/. /opt/

RUN chmod -R g=u -R /home/eduk8s
