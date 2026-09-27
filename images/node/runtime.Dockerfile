ARG BASE=gcr.io/distroless/nodejs22-debian12
FROM ${BASE}
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
WORKDIR /app
USER nonroot
