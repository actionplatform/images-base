FROM python:3.12-slim AS apbuild
COPY pyproject.toml README.md LICENSE /src/
COPY ap_build /src/ap_build
RUN pip install --no-cache-dir --target /opt/ap-build /src

FROM golang:1.23-bookworm
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends make zip python3 \
 && rm -rf /var/lib/apt/lists/*
COPY --from=apbuild /opt/ap-build /opt/ap-build
RUN printf '#!/bin/sh\nexec python3 -m ap_build "$@"\n' > /usr/local/bin/ap-build && chmod +x /usr/local/bin/ap-build
ENV PYTHONPATH=/opt/ap-build CGO_ENABLED=0 GOTOOLCHAIN=auto GOFLAGS=-buildvcs=false
WORKDIR /w
ENTRYPOINT ["ap-build"]
