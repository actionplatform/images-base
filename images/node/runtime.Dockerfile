FROM gcr.io/distroless/nodejs22-debian12
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
WORKDIR /app
USER nonroot
