ARG BASE=ruby:3.3-slim-bookworm
FROM ${BASE}
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
RUN apt-get update -qq && apt-get install -y --no-install-recommends libyaml-0-2 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 65532 nonroot \
 && useradd --system --uid 65532 --gid 65532 --home-dir /app --create-home --no-log-init nonroot
ENV APP_ENV=production RACK_ENV=production BUNDLE_WITHOUT=development:test
WORKDIR /app
USER 65532:65532
