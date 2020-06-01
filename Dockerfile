ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM ${IMAGE_REPOSITORY}/pkgs-java-tools:200601.023308.4090134 as java-tools

FROM ${IMAGE_REPOSITORY}/base-environment:200601.040417.e1f4cba

COPY --from=java-tools --chown=1001:0 /opt/jdk8 /opt/java

COPY --from=java-tools --chown=1001:0 /opt/gradle /opt/gradle

COPY --from=java-tools --chown=1001:0 /opt/maven /opt/maven

COPY --from=java-tools --chown=1001:0 /opt/theia/plugins/. /opt/theia/plugins/

COPY --from=java-tools --chown=1001:0 /home/eduk8s/. /home/eduk8s/

ENV PATH=/opt/java/bin:/opt/gradle/bin:/opt/maven/bin:$PATH \
    JAVA_HOME=/opt/java \
    M2_HOME=/opt/maven
