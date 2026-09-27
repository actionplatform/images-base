ARG BASE=python:3.12-slim
FROM ${BASE}
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
RUN useradd --system --uid 65532 --home /app nonroot
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
USER nonroot
ENTRYPOINT ["python3"]
