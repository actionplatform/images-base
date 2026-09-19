"""ap-build: one verb per step — install, build, test, lint, package, start — the same in every language.

What a verb runs comes from `[build]` in the project's platform.toml; when the project says nothing, the language's convention (read from `[project] language`) does.

`package` produces what a Lambda Web Adapter function runs: the app and its dependencies under `AP_ARTIFACTS`, plus `run.sh` (managed runtimes) with the start command baked in — or `bootstrap` (Go, provided.al2023). `start` runs the command that serves HTTP on `$PORT`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

VERBS = ("install", "build", "test", "lint", "package", "start")
LANGUAGES = ("python", "node", "go", "java", "kotlin", "ruby")

ARCH = os.environ.get("AP_ARCH", "arm64")
PY_PLATFORM = {"arm64": "manylinux2014_aarch64", "x86_64": "manylinux2014_x86_64"}
PY_VERSION = os.environ.get("AP_PYTHON", "3.12")
GO_MAIN = "./cmd/server"

DEFAULTS: dict[str, dict[str, str]] = {
    "python": {
        "install": "poetry install --no-interaction",
        "build": "",
        "test": "poetry run pytest -q",
        "lint": "poetry run ruff check . && poetry run ruff format --check .",
        "start": "python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}",
    },
    "node": {
        "install": "[ -f package-lock.json ] && npm ci --no-audit --no-fund || npm install --no-audit --no-fund",
        "build": "npm run build",
        "test": "npm test",
        "lint": "npm run lint",
        "start": "node dist/server.js",
    },
    "go": {
        "install": "go mod download",
        "build": "go build ./...",
        "test": "go test ./...",
        "lint": "go vet ./...",
        "start": "./bootstrap",
    },
    "java": {
        "install": "mvn -B -q dependency:go-offline",
        "build": "mvn -B -q -DskipTests package",
        "test": "mvn -B -q test",
        "lint": "mvn -B -q checkstyle:check",
        "start": "java -jar app.jar --server.port=${PORT:-8080}",
    },
    "kotlin": {
        "install": "mvn -B -q dependency:go-offline",
        "build": "mvn -B -q -DskipTests package",
        "test": "mvn -B -q test",
        "lint": "mvn -B -q verify -DskipTests",
        "start": "java -jar app.jar --server.port=${PORT:-8080}",
    },
    "ruby": {
        "install": "bundle install",
        "build": "",
        "test": "bundle exec rspec",
        "lint": "bundle exec rubocop",
        "start": "bundle exec rackup -s webrick -o 0.0.0.0 -p ${PORT:-8080}",
    },
}


def manifest_of(root: Path, name: str) -> dict:
    path = root / name

    if not path.exists():
        return {}

    with path.open("rb") as handle:
        return tomllib.load(handle)


def manifest(root: Path) -> dict:
    return manifest_of(root, "platform.toml")


def language_of(root: Path) -> str:
    language = (manifest(root).get("project") or {}).get("language", "")

    if language not in LANGUAGES:
        raise SystemExit(
            f"ap-build: [project] language {language!r} is not one of {', '.join(LANGUAGES)}"
        )

    return language


def command(root: Path, verb: str) -> str:
    """The shell line for `verb`: the project's own under [build], else the language's default. `package` has no default line — it is assembled here."""
    own = (manifest(root).get("build") or {}).get(verb)

    if own is not None:
        return str(own)

    if verb == "package":
        return ""

    return DEFAULTS[language_of(root)][verb]


def sh(line: str, root: Path, env: dict[str, str] | None = None) -> None:
    print(f"$ {line}", flush=True)
    code = subprocess.run(
        ["sh", "-c", line], cwd=root, env={**os.environ, **(env or {})}, check=False
    ).returncode

    if code != 0:
        raise SystemExit(code)


def copy_tree(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True, symlinks=True)
    elif source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_start(root: Path, artifacts: Path, name: str = "run.sh") -> Path:
    script = artifacts / name
    script.write_text(
        f'#!/bin/bash\nset -e\ncd "$(dirname "$0")"\nexec {command(root, "start")}\n'
    )
    script.chmod(0o755)

    return script


def package(root: Path, artifacts: Path) -> None:
    """The app, its dependencies and its start script under `artifacts`, shaped for the Lambda Web Adapter."""
    own = (manifest(root).get("build") or {}).get("package")
    artifacts.mkdir(parents=True, exist_ok=True)

    if own:
        sh(str(own), root, {"AP_ARTIFACTS": str(artifacts)})
        write_start(root, artifacts)

        return

    PACKAGERS[language_of(root)](root, artifacts)


EXCLUDED = {
    ".git",
    ".ap-build",
    ".venv",
    ".code_quality",
    ".github",
    ".gitlab-ci.yml",
    "bitbucket-pipelines.yml",
    "Jenkinsfile",
    "tests",
    "test",
    "spec",
    "dist",
    "target",
    "node_modules",
    "vendor",
    "tmp",
    "log",
    "template.yaml",
    "samconfig.toml",
    "Makefile",
    "requirements",
    "DEPLOY.md",
}


def copy_sources(root: Path, artifacts: Path, extra: set[str] | None = None) -> None:
    skip = EXCLUDED | (extra or set())

    for item in root.iterdir():
        if item.name in skip or item.name.endswith((".lock", ".md")):
            continue

        copy_tree(item, artifacts / item.name)


def package_python(root: Path, artifacts: Path) -> None:
    pip = (
        f'python -m pip install --quiet --upgrade --target "{artifacts}" '
        f"--platform {PY_PLATFORM[ARCH]} --python-version {PY_VERSION} "
        f"--implementation cp --only-binary=:all:"
    )
    poetry = (manifest_of(root, "pyproject.toml").get("tool") or {}).get("poetry") or {}

    if poetry.get("package-mode", True):
        dist = root / ".ap-build" / "dist"
        shutil.rmtree(dist, ignore_errors=True)
        sh(f'poetry build --no-interaction -f wheel -o "{dist}"', root)
        sh(f'{pip} "{dist}"/*.whl', root)
    else:
        requirements = root / ".ap-build" / "requirements.txt"
        requirements.parent.mkdir(parents=True, exist_ok=True)
        sh(
            f'poetry export --no-interaction --only main --without-hashes -f requirements.txt -o "{requirements}"',
            root,
        )
        sh(f'{pip} -r "{requirements}"', root)
        copy_sources(root, artifacts, {"pyproject.toml", "poetry.lock"})

    write_start(root, artifacts)


def package_node(root: Path, artifacts: Path) -> None:
    sh(command(root, "install"), root)
    sh(command(root, "build"), root)
    sh("npm prune --omit=dev --no-audit --no-fund", root)

    for name in ("dist", "node_modules", "package.json"):
        copy_tree(root / name, artifacts / name)

    write_start(root, artifacts)


def package_go(root: Path, artifacts: Path) -> None:
    main = (manifest(root).get("build") or {}).get("main") or GO_MAIN
    sh(
        f'GOOS=linux GOARCH={ARCH} CGO_ENABLED=0 go build -ldflags="-s -w" '
        f'-o "{artifacts}/bootstrap" {main}',
        root,
    )


def package_jvm(root: Path, artifacts: Path) -> None:
    sh(command(root, "build"), root)
    jars = sorted(
        p
        for p in (root / "target").glob("*.jar")
        if not p.name.endswith(("-sources.jar", "-javadoc.jar"))
    )

    if not jars:
        raise SystemExit("ap-build package: mvn package produced no jar under target/")

    shutil.copy2(jars[-1], artifacts / "app.jar")
    write_start(root, artifacts)


def package_ruby(root: Path, artifacts: Path) -> None:
    env = {
        "BUNDLE_PATH": "vendor/bundle",
        "BUNDLE_WITHOUT": "development:test",
        "BUNDLE_DEPLOYMENT": "false",
        "BUNDLE_FROZEN": "false",
    }
    sh("bundle install --quiet", root, env)
    copy_sources(root, artifacts, {".bundle"})
    copy_tree(root / "Gemfile.lock", artifacts / "Gemfile.lock")

    bundle = artifacts / ".bundle"
    bundle.mkdir(exist_ok=True)
    (bundle / "config").write_text(
        'BUNDLE_PATH: "vendor/bundle"\nBUNDLE_WITHOUT: "development:test"\n'
    )
    write_start(root, artifacts)


PACKAGERS = {
    "python": package_python,
    "node": package_node,
    "go": package_go,
    "java": package_jvm,
    "kotlin": package_jvm,
    "ruby": package_ruby,
}


def run(root: Path, verb: str) -> int:
    if verb not in VERBS:
        raise SystemExit(f"ap-build: unknown verb {verb!r}; one of {', '.join(VERBS)}")

    if verb == "package":
        artifacts = Path(
            os.environ.get("AP_ARTIFACTS") or root / ".ap-build" / "package"
        )
        print(f"ap-build package → {artifacts}", flush=True)
        package(root, artifacts)

        return 0

    line = command(root, verb)

    if not line:
        print(f"ap-build {verb}: nothing to do")

        return 0

    print(f"ap-build {verb}: {line}", flush=True)

    return subprocess.run(["sh", "-c", line], cwd=root, check=False).returncode


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
