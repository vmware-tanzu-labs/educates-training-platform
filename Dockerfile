FROM docker:19.03-dind-rootless

USER root

# Can use version 0.15 of crun as it breaks with older Linux kernels.

RUN wget -O /usr/local/bin/crun https://github.com/containers/crun/releases/download/0.14.1/crun-0.14.1-static-x86_64 && chmod +x /usr/local/bin/crun

USER rootless
