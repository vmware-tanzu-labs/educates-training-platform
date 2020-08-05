FROM node:current as node-builder

WORKDIR /work

COPY . /work

RUN npm install && \
    npm run vsce-package

FROM quay.io/eduk8s/pkgs-code-server:200805.044534.6d6c5a5

COPY --chown=1001:0 --from=node-builder /work/eduk8s-vscode-helper-0.0.1.vsix /home/eduk8s

# Note that "/opt/eduk8s/workshop/code-server/extensions" is a temporary
# build location which is convenient as the code-server editor looks in
# this location as one of the places extensions can be installed. When
# the extension is copied into the final workshop base environment image
# it will actually be copied to "/opt/code-server/extensions".

RUN mkdir -p /opt/eduk8s/workshop/code-server/extensions && \
    code-server --extensions-dir /opt/eduk8s/workshop/code-server/extensions --install-extension eduk8s-vscode-helper-0.0.1.vsix

# The routes file exposes the REST API endpoint for the VS code extension
# under /code-server URL path. This will be copied into the final workshop
# base environment image in same location.

COPY --chown=1001:0 routes/. /opt/eduk8s/workshop/gateway/routes/

# The tests are to allow checking the extension works when this container
# image is run, they are not copied into the final workshop base environment
# image

COPY --chown=1001:0 tests/. /home/eduk8s/
