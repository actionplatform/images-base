"""ap-build: one verb per step — install, build, test, lint, package — the same in every language.

What a verb runs comes from `[build]` in the project's platform.toml; when the project says nothing, the language's convention (read from `[project] language`) does.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

VERBS = ("install", "build", "test", "lint", "package")

DEFAULTS: dict[str, dict[str, str]] = {
    "python": {
        "install": "poetry install --no-interaction",
        "build": "",
        "test": "poetry run pytest -q",
        "lint": "poetry run ruff check . && poetry run ruff format --check .",
    },
    "node": {
        "install": "[ -f package-lock.json ] && npm ci --no-audit --no-fund || npm install --no-audit --no-fund",
        "build": "npm run build",
        "test": "npm test",
        "lint": "npm run lint",
    },
    "go": {
        "install": "go mod download",
        "build": "go build ./...",
        "test": "go test ./...",
        "lint": "go vet ./...",
    },
    "java": {
        "install": "mvn -B -q dependency:go-offline",
        "build": "mvn -B -q -DskipTests package",
        "test": "mvn -B -q test",
        "lint": "mvn -B -q checkstyle:check",
    },
    "kotlin": {
        "install": "mvn -B -q dependency:go-offline",
        "build": "mvn -B -q -DskipTests package",
        "test": "mvn -B -q test",
        "lint": "mvn -B -q verify -DskipTests",
    },
    "ruby": {
        "install": "bundle install",
        "build": "",
        "test": "bundle exec rspec",
        "lint": "bundle exec rubocop",
    },
}

PACKAGE = "[ -f Makefile ] && grep -q '^build-ApiFunction' Makefile && make build-ApiFunction ARTIFACTS_DIR=\"${AP_ARTIFACTS:-$PWD/.ap-build/package}\" || echo 'nothing to package: no build-ApiFunction recipe in the Makefile'"


def manifest(root: Path) -> dict:
    path = root / "platform.toml"

    if not path.exists():
        return {}

    with path.open("rb") as handle:
        return tomllib.load(handle)


def command(root: Path, verb: str) -> str:
    """The shell line for `verb`: the project's own under [build], else the language's default."""
    data = manifest(root)
    own = (data.get("build") or {}).get(verb)

    if own is not None:
        return str(own)

    if verb == "package":
        return PACKAGE

    language = (data.get("project") or {}).get("language", "")

    if language not in DEFAULTS:
        raise SystemExit(
            f"ap-build: no [build] {verb} in platform.toml and no default for language {language!r}"
        )

    return DEFAULTS[language][verb]


def run(root: Path, verb: str) -> int:
    if verb not in VERBS:
        raise SystemExit(f"ap-build: unknown verb {verb!r}; one of {', '.join(VERBS)}")

    line = command(root, verb)

    if not line:
        print(f"ap-build {verb}: nothing to do")

        return 0

    print(f"ap-build {verb}: {line}", flush=True)
    artifacts = Path(os.environ.get("AP_ARTIFACTS") or root / ".ap-build" / "package")

    if verb == "package":
        artifacts.mkdir(parents=True, exist_ok=True)

    return subprocess.run(
        ["sh", "-c", line],
        cwd=root,
        env={**os.environ, "AP_ARTIFACTS": str(artifacts)},
        check=False,
    ).returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in ("-h", "--help"):
        print(f"usage: ap-build <{'|'.join(VERBS)}> [more verbs]")

        return 0 if args else 2

    for verb in args:
        code = run(Path.cwd(), verb)

        if code != 0:
            return code

    return 0


if __name__ == "__main__":
    sys.exit(main())
