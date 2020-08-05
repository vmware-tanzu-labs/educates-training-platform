FROM node:current as node-builder

WORKDIR /work

COPY . /work

RUN npm install && \
    npm run vsce-package

FROM quay.io/eduk8s/pkgs-code-server:200728.051939.d3734df

COPY --chown=1001:0 --from=node-builder /work/eduk8s-vscode-helper-0.0.1.vsix /home/eduk8s

# Note that "/opt/eduk8s/workshop/code-server/extensions" is a temporary
# build location which is convenient as the code-server editor looks in
# this location as one of the places extensions can be installed. When
# the extension is copied into the final workshop base environment image
# it will actually be copied to "/opt/code-server/extensions".

RUN mkdir -p /opt/eduk8s/workshop/code-server/extensions && \
    code-server --extensions-dir /opt/eduk8s/workshop/code-server/extensions --install-extension eduk8s-vscode-helper-0.0.1.vsix

# The "humao.rest-client" extension is to help testing and is not copied
# to the final workshop base environment image. The "humao.rest-client"
# extension will be later added to the base code-server installation so
# this will not be required at that point.

RUN code-server --install-extension humao.rest-client

COPY --chown=1001:0 tests/. /home/eduk8s/
