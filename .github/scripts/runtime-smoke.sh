#!/usr/bin/env bash
# runtime-smoke.sh <language> <version> <build base> <runtime base> <template dir> <templates repo>
# Builds build-<language>:<version> and runtime-<language>:<version>, renders the template with the
# docker overlay, builds the app's image from them the way an app does, runs it and calls /health.
set -euo pipefail

language=$1 version=$2 build_base=$3 runtime_base=$4 template=$5 templates=$6
image=ghcr.io/actionplatform
work=$(mktemp -d "$PWD/.smoke.XXXXXX")
trap 'docker rm -f smoke-app >/dev/null 2>&1 || true; rm -rf "$work"' EXIT

docker build -q -f "images/$language/Dockerfile" --build-arg "BASE=$build_base" -t "$image/build-$language:$version" . >/dev/null
docker build -q -f "images/$language/runtime.Dockerfile" --build-arg "BASE=$runtime_base" -t "$image/runtime-$language:$version" . >/dev/null

cookiecutter --no-input -o "$work" "$templates/$template" project_name=demo "_${language}_version=$version" >/dev/null
cookiecutter --no-input -o "$work/overlay" "$templates/cloud/docker" project_name=demo "language=$language" type=web ci=github >/dev/null
cp -R "$work/overlay/demo/." "$work/demo/"

if [ "$language" = python ]; then
  docker run --rm -v "$work/demo:/w" --entrypoint poetry "$image/build-$language:$version" lock --no-interaction >/dev/null
fi

arg="$(printf '%s' "$language" | tr '[:lower:]' '[:upper:]')_VERSION"
docker build -q --build-arg "$arg=$version" -t smoke-app "$work/demo" >/dev/null
docker run -d --name smoke-app -p 18000:8000 smoke-app >/dev/null

for _ in $(seq 1 30); do
  if body=$(curl -fsS http://localhost:18000/health 2>/dev/null); then
    echo "$language $version: /health -> $body"
    exit 0
  fi
  sleep 2
done

echo "$language $version: /health never answered" >&2
docker logs smoke-app 2>&1 | tail -30 >&2
exit 1
