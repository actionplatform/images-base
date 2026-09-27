# syntax=docker/dockerfile:1
ARG BASE=python:3.12-slim
FROM ${BASE}
LABEL org.opencontainers.image.source="https://github.com/actionplatform/images-base"
ENV VIRTUAL_ENV=/opt/tools \
    PATH="/opt/tools/bin:${PATH}" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    SAM_CLI_TELEMETRY=0
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends git make zip curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && python -m venv "$VIRTUAL_ENV"
COPY images/python/tools.txt /tmp/tools.txt
COPY pyproject.toml README.md LICENSE /src/
COPY ap_build /src/ap_build
RUN python -m pip install --no-cache-dir -r /tmp/tools.txt /src && rm -rf /src /tmp/tools.txt
WORKDIR /w
ENTRYPOINT ["ap-build"]
