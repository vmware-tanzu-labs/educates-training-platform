FROM node:current as node-builder

WORKDIR /work

COPY . /work

RUN npm install && \
    npm run vsce-package

FROM scratch

COPY --chown=1001:0 --from=node-builder /work/eduk8s-vscode-helper-0.0.1.vsix /opt/code-server/extensions/

COPY --chown=1001:0 setup.d/. /opt/code-server/setup.d/

COPY --chown=1001:0 routes/. /opt/eduk8s/workshop/gateway/routes/
