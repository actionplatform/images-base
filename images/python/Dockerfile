FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends git make zip curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE /src/
COPY ap_build /src/ap_build
RUN pip install --no-cache-dir /src "poetry>=1.8" poetry-plugin-export aws-sam-cli && rm -rf /src
ENV POETRY_VIRTUALENVS_IN_PROJECT=true SAM_CLI_TELEMETRY=0
WORKDIR /w
ENTRYPOINT ["ap-build"]
