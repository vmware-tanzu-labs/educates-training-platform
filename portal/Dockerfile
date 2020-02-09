FROM getwarped/warp0-debian10-python37:latest

COPY --chown=1001:0 . /opt/app-root/src

RUN assemble-image

CMD [ "start-container" ]

EXPOSE 8080
