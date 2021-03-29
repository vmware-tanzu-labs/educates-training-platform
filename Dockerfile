ARG IMAGE_REPOSITORY=quay.io/eduk8s

FROM ${IMAGE_REPOSITORY}/base-environment:210329.053124.f3d550c

USER root

RUN HOME=/root && \
    INSTALL_PKGS=" \
        @xfce-desktop-environment \
        chromium \
        chromium-libs \
        chromium-libs-media \
        novnc \
        firefox \
        tigervnc-server \
        xterm \
        xdotool \
    " && \
    dnf install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    dnf remove -y '*power*' '*screensaver*' && \
    dnf clean -y --enablerepo='*' all

RUN ln -s /usr/bin/chromium-browser /usr/bin/google-chrome

RUN sed -i '$s/CHROMIUM_FLASH_FLAGS /CHROMIUM_FLASH_FLAGS --no-sandbox --start-maximized --user-data-dir /' /usr/lib64/chromium-browser/chromium-browser.sh

RUN rm /etc/xdg/autostart/xfce-polkit*

USER 1001

COPY --chown=1001 vncserver.conf /opt/eduk8s/etc/supervisor/vncserver.conf
COPY --chown=1001 novnc.conf /opt/eduk8s/etc/supervisor/novnc.conf

COPY --chown=1001 start-vncserver /opt/eduk8s/sbin/start-vncserver
COPY --chown=1001 start-novnc /opt/eduk8s/sbin/start-novnc

COPY --chown=1001 xfce4-helpers.rc /home/eduk8s/.config/xfce4/helpers.rc

RUN mkdir /home/eduk8s/.vnc
COPY --chown=1001 xstartup /home/eduk8s/.vnc/xstartup
RUN chmod -v +x /home/eduk8s/.vnc/xstartup
RUN echo eduk8s | vncpasswd -f > /home/eduk8s/.vnc/passwd
RUN chmod 600 /home/eduk8s/.vnc/passwd
