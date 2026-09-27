ARG BASE=gcr.io/distroless/java21-debian12
FROM ${BASE}
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
WORKDIR /app
USER nonroot
