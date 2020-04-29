FROM quay.io/eduk8s/workshop-dashboard:master

RUN mkdir /opt/java && \
    curl -sL -o /tmp/jdk.tar.gz https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.7%2B10/OpenJDK11U-jdk_x64_linux_hotspot_11.0.7_10.tar.gz && \
    echo "ee60304d782c9d5654bf1a6b3f38c683921c1711045e1db94525a51b7024a2ca /tmp/jdk.tar.gz" | sha256sum --check --status && \
    tar -C /opt/java --strip-components 1 -zxf /tmp/jdk.tar.gz && \
    rm /tmp/jdk.tar.gz

RUN curl -sL -o /tmp/maven.tar.gz http://www.us.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz && \
    echo "c35a1803a6e70a126e80b2b3ae33eed961f83ed74d18fcd16909b2d44d7dada3203f1ffe726c17ef8dcca2dcaa9fca676987befeadc9b9f759967a8cb77181c0 /tmp/maven.tar.gz" | sha512sum --check --status && \
    tar -C /opt/java --strip-components 1 -zxf /tmp/maven.tar.gz && \
    rm -rf /opt/java/lib/ext && \
    rm /tmp/maven.tar.gz

RUN curl -sL -o /tmp/gradle.zip https://services.gradle.org/distributions/gradle-6.3-bin.zip && \
    echo "038794feef1f4745c6347107b6726279d1c824f3fc634b60f86ace1e9fbd1768 /tmp/gradle.zip" | sha256sum --check --status && \
    unzip -d /opt/java /tmp/gradle.zip && \
    cp -rn /opt/java/gradle-6.3/{init.d,bin,lib} /opt/java && \
    rm -rf /opt/java/gradle-6.3 && \
    rm /tmp/gradle.zip

ENV PATH=/opt/java/bin:$PATH \
    JAVA_HOME=/opt/java
