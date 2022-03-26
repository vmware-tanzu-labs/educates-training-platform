ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM ${IMAGE_REPOSITORY}/pkgs-java-tools:220303.010935.e373f7a AS java-tools

FROM ${IMAGE_REPOSITORY}/base-environment:220308.031150.7abc4b2

COPY --from=java-tools --chown=1001:0 /opt/jdk11 /opt/java

COPY --from=java-tools --chown=1001:0 /opt/gradle /opt/gradle

COPY --from=java-tools --chown=1001:0 /opt/maven /opt/maven

COPY --from=java-tools --chown=1001:0 /opt/code-server/.  /opt/code-server/

COPY --from=java-tools --chown=1001:0 /home/eduk8s/. /home/eduk8s/

COPY --from=java-tools --chown=1001:0 /opt/eduk8s/. /opt/eduk8s/

ENV PATH=/opt/java/bin:/opt/gradle/bin:/opt/maven/bin:$PATH \
    JAVA_HOME=/opt/java \
    M2_HOME=/opt/maven