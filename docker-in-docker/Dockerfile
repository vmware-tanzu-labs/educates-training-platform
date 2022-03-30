FROM docker:20.10.14-dind-rootless

USER root

RUN wget -O /usr/local/bin/crun https://github.com/containers/crun/releases/download/1.4.4/crun-1.4.4-linux-amd64 && chmod +x /usr/local/bin/crun

# Link standard location of docker socket to where it will exist in the
# mounted volume. This is so that mounting docker socket in a container
# will work.

RUN mkdir /var/run/workshop && \
    ln -s /var/run/workshop/docker.sock /var/run/docker.sock

USER rootless
