ARG BASE=python:3.12-slim
FROM ${BASE}
LABEL org.opencontainers.image.source="https://github.com/actionplatform/images-base"
RUN groupadd --system --gid 65532 nonroot \
 && useradd --system --uid 65532 --gid 65532 --home-dir /app --create-home --no-log-init nonroot
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
USER 65532:65532
ENTRYPOINT ["python3"]
