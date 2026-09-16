FROM ruby:3.3-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/actionplatform/images-base
RUN apt-get update -qq && apt-get install -y --no-install-recommends libyaml-0-2 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --uid 65532 --home /app nonroot
ENV APP_ENV=production RACK_ENV=production BUNDLE_WITHOUT=development:test
WORKDIR /app
USER nonroot
