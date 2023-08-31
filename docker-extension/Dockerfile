ARG REPOSITORY=localhost:5001
ARG CLI_IMAGE_NAME=educates-client-programs
ARG TAG=latest

FROM ${REPOSITORY}/${CLI_IMAGE_NAME}:${TAG} AS client-programs

FROM golang:1.19-alpine AS builder
ENV CGO_ENABLED=0
WORKDIR /backend
COPY backend/go.* .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download
COPY backend/. .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -trimpath -ldflags="-s -w" -o bin/service

FROM --platform=$BUILDPLATFORM node:18.12-alpine3.16 AS client-builder
WORKDIR /ui
# cache packages in layer
COPY ui/package.json /ui/package.json
COPY ui/package-lock.json /ui/package-lock.json
RUN --mount=type=cache,target=/usr/src/app/.npm \
    npm set cache /usr/src/app/.npm && \
    npm ci
# install
COPY ui /ui
RUN npm run build

FROM bitnami/minideb:bullseye

ARG TARGETARCH

LABEL org.opencontainers.image.title="Educates Docker Desktop Extension" \
    org.opencontainers.image.description="Spin up a local Educates Training Platform workshop" \
    org.opencontainers.image.vendor="VMware" \
    org.opencontainers.image.licenses="Apache-2.0" \
    com.docker.desktop.extension.api.version="0.3.4" \
    com.docker.extension.screenshots="" \
    com.docker.desktop.extension.icon="https://raw.githubusercontent.com/vmware-tanzu-labs/educates-training-platform/develop/workshop-images/base-environment/opt/gateway/src/frontend/images/logo.png" \
    com.docker.extension.detailed-description="Spin up a local Educates Training Platform workshop" \
    com.docker.extension.publisher-url="https://github.com/vmware-tanzu-labs/educates-training-platform" \
    com.docker.extension.additional-urls="" \
    com.docker.extension.categories="" \
    com.docker.extension.changelog=""

COPY --from=client-programs educates-linux-${TARGETARCH} /educates

COPY --from=builder /backend/bin/service /

COPY docker-compose.yaml .
COPY metadata.json .
COPY logo.svg .
COPY --from=client-builder /ui/build ui

CMD /service -socket /run/guest-services/backend.sock

# CMD ["/educates", "docker", "extension", "backend", "--socket", "/run/guest-services/backend.sock"]
