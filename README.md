# images-base

Build and runtime base images for every language the [templates](https://github.com/actionplatform/templates) produce — the same five verbs everywhere:

```bash
docker run --rm -v "$PWD:/w" ghcr.io/actionplatform/build-node install build test lint package
```

| Image | Toolchain | Runtime image |
|---|---|---|
| `build-python` | Python 3.12, poetry, aws-sam-cli | `runtime-python` — distroless python3 |
| `build-node` | Node 22, npm | `runtime-node` — distroless nodejs22 |
| `build-go` | Go 1.23 | `runtime-go` — distroless static |
| `build-java` | JDK 21, Maven 3.9 (Java and Kotlin) | `runtime-java` — distroless java21 |
| `build-ruby` | Ruby 3.3, bundler, a compiler for native gems | `runtime-ruby` — `ruby:3.3-slim`, non-root (no distroless Ruby exists) |

Published on `ghcr.io/actionplatform/<image>` (and Docker Hub when configured) as `<major>`, `<major.minor>`, `<version>` and `latest`, for `linux/amd64` and `linux/arm64`.

## ap-build

The entrypoint. `ap-build <verb>…` runs, in the current directory, what `[build]` in `platform.toml` says for the verb — the language's convention when the project says nothing:

```toml
[build]
install = "npm ci"
test    = "vitest run"
```

| Verb | python | node | go | java · kotlin | ruby |
|---|---|---|---|---|---|
| `install` | `poetry install` | `npm ci` | `go mod download` | `mvn dependency:go-offline` | `bundle install` |
| `build` | — | `npm run build` | `go build ./...` | `mvn -DskipTests package` | — |
| `test` | `pytest` | `npm test` | `go test ./...` | `mvn test` | `bundle exec rspec` |
| `lint` | `ruff check && ruff format --check` | `npm run lint` | `go vet ./...` | `mvn checkstyle:check` | `bundle exec rubocop` |
| `package` | `make build-ApiFunction` when the Makefile has it (the `aws/lambda` overlay's recipe), into `AP_ARTIFACTS` (default `.ap-build/package`) | same | same | same | same |

A verb prints the line it runs and exits with its status; an empty line is a no-op. `pip install .` gives the same command on a machine without Docker.

## Runtime images

A container-shipped app ends in the language's runtime image:

```dockerfile
FROM ghcr.io/actionplatform/build-node AS build
COPY . .
RUN ap-build install build

FROM ghcr.io/actionplatform/runtime-node
COPY --from=build /w/dist /app/dist
COPY --from=build /w/node_modules /app/node_modules
CMD ["dist/server.js"]
```

Lambda packages keep the managed runtimes; distroless is for containers.

## The contract with the templates

CI renders one web template per language from `actionplatform/templates`, lays the `aws/lambda` overlay on it and runs all five verbs inside the freshly built image — a template and its image cannot drift apart unnoticed.

## Releasing

`action-platform release` cuts `vX.Y.Z`; the tag publishes every image.
