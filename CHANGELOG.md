# Changelog

## v0.3.0 — 2026-09-27

### Bug Fixes
- **runtime:** /app belongs to the non-root user in Python and Ruby
- **ap-build:** the JVM package ships the jar it was told, or stops
- **ap-build:** a Python package installs poetry.lock's versions
- **ap-build:** the Ruby package carries its installed gems
- **build-python:** pinned tools in a venv; AP_PYTHON from the interpreter

### Docs
- **readme:** six verbs, moving tags, the runtime contract

### Tests
- import ap_build at the top

### CI
- run every runtime image with a real app before it ships
- **publish:** images publish from a vX.Y.Z tag only

### Style
- format ap_build

## v0.2.1 — 2026-09-27

### Bug Fixes
- **ap-build:** go build takes amd64, not x86_64

## v0.2.0 — 2026-09-27

### Features
- **images:** one image per language version, tagged by it
- **ap-build:** run on Python 3.10 and newer

## v0.1.0 — 2026-09-19

### Features
- **ap-build:** start verb and a per-language package for the Lambda Web Adapter

### Bug Fixes
- **ap-build:** package projects poetry does not build, and take the overlay from the plugin in CI

## v0.0.2 — 2026-09-16

### CI
- **publish:** ghcr only — the secrets expression made the workflow invalid

## v0.0.1 — 2026-09-16

### Features
- build and runtime base images for python, node, go, java and ruby with the ap-build entrypoint

### CI
- ruff rule set, check=False on subprocess; README with the icons
