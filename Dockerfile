FROM node:current as node-builder

WORKDIR /work

COPY . /work

RUN npm install && \
    npm run vsce-package


# FROM node:current as initializr-builder

# RUN mkdir /work
# WORKDIR /work
# ADD https://github.com/BoykoAlex/vscode-spring-initializr/archive/customize.zip /work/initializr-extension.zip
# RUN unzip initializr-extension.zip 
# RUN rm initializr-extension.zip
# RUN cd vscode-spring-initializr-* \
#     && npm install \
#     && npm install vsce --save-dev \
#     && ./node_modules/.bin/vsce package \
#     && mv *.vsix /work

FROM quay.io/eduk8s/pkgs-code-server:220228.024126.bb3a110

COPY --chown=1001:0 --from=node-builder /work/eduk8s-vscode-helper-0.0.1.vsix /home/eduk8s
# COPY --chown=1001:0 --from=initializr-builder /work/vscode-spring-initializr-0.4.8.vsix /home/eduk8s

# Note that "/opt/eduk8s/workshop/code-server/extensions" is a temporary
# build location which is convenient as the code-server editor looks in
# this location as one of the places extensions can be installed. When
# the extension is copied into the final workshop base environment image
# it will actually be copied to "/opt/code-server/extensions".

RUN mkdir -p /opt/eduk8s/workshop/code-server/extensions && \
    code-server --extensions-dir /opt/eduk8s/workshop/code-server/extensions --install-extension eduk8s-vscode-helper-0.0.1.vsix

#RUN code-server --extensions-dir /opt/eduk8s/workshop/code-server/extensions --install-extension vscode-spring-initializr-0.4.8.vsix

# The routes file exposes the REST API endpoint for the VS code extension
# under /code-server URL path. This will be copied into the final workshop
# base environment image in same location.

COPY --chown=1001:0 routes/. /opt/eduk8s/workshop/gateway/routes/

# The tests are to allow checking the extension works when this container
# image is run, they are not copied into the final workshop base environment
# image

COPY --chown=1001:0 tests/. /home/eduk8s/
