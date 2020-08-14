ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM ${IMAGE_REPOSITORY}/pkgs-java-tools:200812.044724.dbe0db7 as java-tools

FROM ${IMAGE_REPOSITORY}/base-environment:200814.035845.28815a3

COPY --from=java-tools --chown=1001:0 /opt/jdk11 /opt/java

COPY --from=java-tools --chown=1001:0 /opt/gradle /opt/gradle

COPY --from=java-tools --chown=1001:0 /opt/maven /opt/maven

COPY --from=java-tools --chown=1001:0 /opt/code-server/extensions/.  /opt/code-server/extensions/

COPY --from=java-tools --chown=1001:0 /home/eduk8s/. /home/eduk8s/

ENV PATH=/opt/java/bin:/opt/gradle/bin:/opt/maven/bin:$PATH \
    JAVA_HOME=/opt/java \
    M2_HOME=/opt/maven
