<p align="center">
  <img src="assets/icons/docker.svg" width="72" alt="">
</p>

<h1 align="center">images-base</h1>

<p align="center">Build and runtime base images for every language the <a href="https://github.com/actionplatform/templates">templates</a> produce — one entrypoint, five verbs, the same everywhere.</p>

```bash
docker run --rm -v "$PWD:/w" ghcr.io/actionplatform/build-node install build test lint package
```

## Images

| | Build image | Versions (**default**) | Toolchain | Runtime image |
|:-:|---|---|---|---|
| <img src="assets/icons/python.svg" width="28" alt="Python"> | `build-python` | 3.10 · 3.11 · **3.12** · 3.13 · 3.14 | <img src="assets/icons/poetry.svg" width="14" alt=""> poetry · aws-sam-cli | `runtime-python` — `python:<version>-slim`, non-root, `python3` as entrypoint (distroless ships only the Debian Python) |
| <img src="assets/icons/nodejs.svg" width="28" alt="Node.js"> | `build-node` | **22** · 24 · 26 | <img src="assets/icons/npm.svg" width="14" alt=""> npm | `runtime-node` — distroless `nodejs<version>` |
| <img src="assets/icons/go.svg" width="28" alt="Go"> | `build-go` | 1.26 · **1.27** | `GOTOOLCHAIN=auto`, `CGO_ENABLED=0` | `runtime-go` — distroless `static` |
| <img src="assets/icons/java.svg" width="28" alt="Java"> <img src="assets/icons/kotlin.svg" width="28" alt="Kotlin"> | `build-java` | 17 · **21** · 25 | <img src="assets/icons/maven.svg" width="14" alt=""> Maven 3.9 — Java and Kotlin | `runtime-java` — distroless `java<version>` |
| <img src="assets/icons/ruby.svg" width="28" alt="Ruby"> | `build-ruby` | **3.3** · 3.4 · 4.0 | bundler · a compiler for native gems | `runtime-ruby` — `ruby:<version>-slim`, non-root (no distroless Ruby exists) |

Every build image also carries `git`, `make`, `zip` and `ap-build` — `make` for `sam build`'s Makefile, `git` and `curl` for CI jobs that run inside the image. `build-python` installs its tools — poetry, poetry-plugin-export, aws-sam-cli — at the exact versions in [`images/python/tools.txt`](images/python/tools.txt) (Dependabot bumps them), in a virtualenv at `/opt/tools`, apart from the interpreter's own packages. `AP_PYTHON` defaults to the interpreter's version, so a Lambda package targets the Python the image runs.

The build images run as root on purpose: CI jobs and `docker run -v "$PWD:/w"` write into a mounted checkout owned by the host's user, which a fixed non-root user inside the image cannot write. The runtime images run as `nonroot`. Upstream images are followed by tag (`python:3.12-slim`), not digest, so a rebuild picks up their security fixes; an app pins what it runs through the immutable `<version>-<release>` tags. The build and runtime images of one version run the same language version. [`versions.json`](versions.json) lists each language's versions, the upstream image each one starts from, and the default.

Published on `ghcr.io/actionplatform/<image>` for `linux/amd64` and `linux/arm64`:

| Tag | Example | Is |
|---|---|---|
| `<language version>` | `build-python:3.13` | that language version, newest images-base release |
| `<language version>-<release>` | `build-python:3.13-0.2.0` | that language version, pinned to an images-base release (`-0.2` follows its patches) |
| `<release>`, `<major.minor>`, `<major>`, `latest` | `build-python:0` | the language's **default** version |

A Dockerfile picks the version with an argument:

```dockerfile
ARG PYTHON_VERSION=3.12
FROM ghcr.io/actionplatform/build-python:${PYTHON_VERSION} AS build
```

## ap-build

The entrypoint. `ap-build <verb>…` runs, in the current directory, what `[build]` in `platform.toml` says for the verb — the language's convention when the project says nothing:

```toml
[build]
install = "npm ci"
test    = "vitest run"
start   = "node dist/server.js"
```

| Verb | <img src="assets/icons/python.svg" width="14" alt=""> python | <img src="assets/icons/nodejs.svg" width="14" alt=""> node | <img src="assets/icons/go.svg" width="14" alt=""> go | <img src="assets/icons/java.svg" width="14" alt=""> java · kotlin | <img src="assets/icons/ruby.svg" width="14" alt=""> ruby |
|---|---|---|---|---|---|
| `install` | `poetry install` | `npm ci` | `go mod download` | `mvn dependency:go-offline` | `bundle install` |
| `build` | — | `npm run build` | `go build ./...` | `mvn -DskipTests package` | — |
| `test` | `pytest` | `npm test` | `go test ./...` | `mvn test` | `bundle exec rspec` |
| `lint` | `ruff check && ruff format --check` | `npm run lint` | `go vet ./...` | `mvn checkstyle:check` | `bundle exec rubocop` |
| `start` | `uvicorn app:app --port $PORT` | `node dist/server.js` | `./bootstrap` | `java -jar app.jar --server.port=$PORT` | `rackup -s webrick -p $PORT` |
| `package` | wheel + deps for the target platform | `dist/` + pruned `node_modules` | static `bootstrap` from `./cmd/server` | `target/*.jar` → `app.jar` | app + `vendor/bundle` |

`package` assembles what a **Lambda Web Adapter** function runs, under `AP_ARTIFACTS` (default `.ap-build/package`): the app, its dependencies and `run.sh` — `exec <start>` — for the managed runtimes, or `bootstrap` for Go on `provided.al2023`. `AP_ARCH` (`arm64`, default, or `x86_64`) and `AP_PYTHON` (`3.12`) pick the target. A project with its own `[build] package` line runs that instead and still gets `run.sh`; `[build] main` names the Go package to build; `[build] jar` the jar to ship when `target/` holds more than one (Java and Kotlin stop otherwise).

The contract every web project honours: **serve HTTP on `$PORT`**. That is what lets one cloud overlay deploy every language.

A verb prints the line it runs and exits with its status; an empty line is a no-op. `pip install .` gives the same command on a machine without Docker.

## Runtime images

A container-shipped app ends in the language's runtime image — two stages, the same shape for every language:

```dockerfile
ARG NODE_VERSION=22
FROM ghcr.io/actionplatform/build-node:${NODE_VERSION} AS build
COPY . .
RUN ap-build install build

FROM ghcr.io/actionplatform/runtime-node:${NODE_VERSION}
COPY --from=build /w/dist /app/dist
COPY --from=build /w/node_modules /app/node_modules
CMD ["dist/server.js"]
```

Lambda packages keep the managed runtimes (`python3.12`, `nodejs22.x`, `java17`, `provided.al2023`, `ruby3.3`); distroless is for containers.

## Who uses it

| Where | How |
|---|---|
| the platform's worker | `ap-build package` — the artefact `sam deploy` ships |
| CI (`ci-github`, `ci-gitlab`, `ci-jenkins`) | `container: ghcr.io/actionplatform/build-<lang>` and `ap-build test lint` — one workflow shape for every language |
| a developer's machine | `docker run … ap-build test`, or the toolchain already there and the same verbs |

## The contract with the templates

CI renders one web template per language from `actionplatform/templates` **for every version in `versions.json`** (the template's `_<language>_version` set to it), lays the `aws/lambda` overlay on it and runs all five verbs inside the freshly built image — a template and its image cannot drift apart unnoticed. `ap-build` itself runs on Python 3.10 and newer, so it works inside every Python image.

## Releasing

`action-platform release` cuts `vX.Y.Z`; the tag publishes every image. The strategy behind the repository: [images-base.md](https://github.com/actionplatform/strategy/blob/main/images-base.md).
