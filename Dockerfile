FROM fedora:35 as java-base

USER root

RUN HOME=/root && \
    INSTALL_PKGS=" \
        findutils \
        unzip \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf clean -y --enablerepo='*' all && \
    useradd -u 1001 -g 0 -M -d /home/eduk8s eduk8s && \
    mkdir -p /home/eduk8s && \
    chown -R 1001:0 /home/eduk8s && \
    chmod -R g=u /home/eduk8s && \
    chmod g+w /etc/passwd && \
    chown 1001:0 /opt

USER 1001

RUN mkdir -p /opt/{jdk8,jdk11,gradle,maven}

RUN curl -sL -o /tmp/jdk8.tar.gz https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/jdk8u292-b10/OpenJDK8U-jdk_x64_linux_hotspot_8u292b10.tar.gz && \
    echo "0949505fcf42a1765558048451bb2a22e84b3635b1a31dd6191780eeccaa4ada /tmp/jdk8.tar.gz" | sha256sum --check --status && \
    tar -C /opt/jdk8 --strip-components 1 -zxf /tmp/jdk8.tar.gz && \
    rm /tmp/jdk8.tar.gz

RUN curl -sL -o /tmp/jdk11.tar.gz https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.9.1%2B1/OpenJDK11U-jdk_x64_linux_hotspot_11.0.9.1_1.tar.gz && \
    echo "e388fd7f3f2503856d0b04fde6e151cbaa91a1df3bcebf1deddfc3729d677ca3 /tmp/jdk11.tar.gz" | sha256sum --check --status && \
    tar -C /opt/jdk11 --strip-components 1 -zxf /tmp/jdk11.tar.gz && \
    rm /tmp/jdk11.tar.gz

RUN curl -sL -o /tmp/maven.tar.gz https://dlcdn.apache.org/maven/maven-3/3.8.4/binaries/apache-maven-3.8.4-bin.tar.gz && \
    echo "a9b2d825eacf2e771ed5d6b0e01398589ac1bfa4171f36154d1b5787879605507802f699da6f7cfc80732a5282fd31b28e4cd6052338cbef0fa1358b48a5e3c8 /tmp/maven.tar.gz" | sha512sum --check --status && \
    tar -C /opt/maven --strip-components 1 -zxf /tmp/maven.tar.gz && \
    rm /tmp/maven.tar.gz

RUN curl -sL -o /tmp/gradle.zip https://services.gradle.org/distributions/gradle-7.4-bin.zip && \
    echo "8cc27038d5dbd815759851ba53e70cf62e481b87494cc97cfd97982ada5ba634 /tmp/gradle.zip" | sha256sum --check --status && \
    unzip -d /opt/gradle /tmp/gradle.zip && \
    mv /opt/gradle/gradle-7.4/* /opt/gradle/ && \
    rm -rf /opt/gradle/gradle-7.4 && \
    rm /tmp/gradle.zip

ENV PATH=/opt/jdk11/bin:/opt/gradle/bin:/opt/maven/bin:$PATH \
    JAVA_HOME=/opt/jdk11 \
    M2_HOME=/opt/maven

WORKDIR /home/eduk8s

#FROM java-base as mvn-wrapper

#RUN mvn -N io.takari:maven:0.7.7:wrapper && \
#    /home/eduk8s/mvnw -v

#FROM java-base as gradle-wrapper

#RUN gradle wrapper --gradle-version=7.4 --distribution-type=bin

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

FROM java-base AS java-tools

#COPY --chown=1001:0 --from=mvn-wrapper /home/eduk8s/.m2 /home/eduk8s/.m2

#COPY --chown=1001:0 --from=gradle-wrapper /home/eduk8s/.gradle /home/eduk8s/.gradle

COPY --chown=1001:0 --from=code-server /opt/code-server/java-extensions/. /opt/code-server/extensions/

COPY --chown=1001:0 opt/. /opt/

#RUN chmod -R g=u -R /home/eduk8s

FROM scratch

COPY --from=java-tools --chown=1001:100 /opt/. /opt/
