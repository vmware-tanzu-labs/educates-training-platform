FROM docker:19.03-dind-rootless

USER root

# Can use version 0.15 of crun as it breaks with older Linux kernels.

RUN wget -O /usr/local/bin/crun https://github.com/containers/crun/releases/download/0.15.1/crun-0.15.1-linux-amd64 && chmod +x /usr/local/bin/crun

# Link standard location of docker socket to where it will exist in the
# mounted volume. This is so that mounting docker socket in a container
# will work.

RUN mkdir /var/run/workshop && \
    ln -s /var/run/workshop/docker.sock /var/run/docker.sock

USER rootless
