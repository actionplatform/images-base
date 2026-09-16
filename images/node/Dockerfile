FROM python:3.12-slim AS apbuild
COPY pyproject.toml README.md LICENSE /src/
COPY ap_build /src/ap_build
RUN pip install --no-cache-dir --target /opt/ap-build /src

FROM node:22-bookworm-slim
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends git make zip curl ca-certificates python3 \
 && rm -rf /var/lib/apt/lists/*
COPY --from=apbuild /opt/ap-build /opt/ap-build
RUN printf '#!/bin/sh\nexec python3 -m ap_build "$@"\n' > /usr/local/bin/ap-build && chmod +x /usr/local/bin/ap-build
ENV PYTHONPATH=/opt/ap-build
WORKDIR /w
ENTRYPOINT ["ap-build"]
