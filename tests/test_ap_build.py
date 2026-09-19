import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ap_build import (  # noqa: E402
    DEFAULTS,
    LANGUAGES,
    PACKAGERS,
    VERBS,
    command,
    main,
    package,
)


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write(self, text: str) -> None:
        (self.root / "platform.toml").write_text(text)

    def test_the_project_wins_over_the_language_default(self):
        self.write('[project]\nlanguage = "node"\n\n[build]\ntest = "vitest run"\n')

        self.assertEqual(command(self.root, "test"), "vitest run")
        self.assertEqual(command(self.root, "build"), "npm run build")

    def test_every_language_answers_every_verb(self):
        for language in ("python", "node", "go", "java", "kotlin", "ruby"):
            self.write(f'[project]\nlanguage = "{language}"\n')

            for verb in VERBS:
                command(self.root, verb)

    def test_an_unknown_language_without_build_section_is_refused(self):
        self.write('[project]\nlanguage = "cobol"\n')

        with self.assertRaises(SystemExit):
            command(self.root, "test")

    def test_package_runs_the_project_recipe_from_the_cli(self):
        self.write(
            '[project]\nlanguage = "go"\n\n[build]\npackage = "echo built > \\"$AP_ARTIFACTS/marker\\""\n'
        )
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)

        self.assertEqual(main(["package"]), 0)
        self.assertEqual(
            (self.root / ".ap-build" / "package" / "marker").read_text().strip(),
            "built",
        )

    def test_an_empty_verb_is_a_no_op(self):
        self.write('[project]\nlanguage = "python"\n')
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)

        self.assertEqual(main(["build"]), 0)

    def test_the_cli_reports_a_failing_command(self):
        self.write('[project]\nlanguage = "go"\n\n[build]\ntest = "exit 3"\n')
        result = subprocess.run(
            [sys.executable, "-m", "ap_build", "test"],
            cwd=self.root,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            check=False,
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("ap-build test: exit 3", result.stdout)


class PackageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_a_project_recipe_runs_and_gets_a_start_script(self):
        (self.root / "platform.toml").write_text(
            '[project]\nlanguage = "node"\n\n[build]\npackage = "echo built > \\"$AP_ARTIFACTS/marker\\""\nstart = "node server.js"\n'
        )
        artifacts = self.root / "out"

        package(self.root, artifacts)

        self.assertEqual((artifacts / "marker").read_text().strip(), "built")
        script = (artifacts / "run.sh").read_text()
        self.assertIn("exec node server.js", script)
        self.assertTrue(os.access(artifacts / "run.sh", os.X_OK))

    def test_every_language_has_a_start_and_a_packager(self):
        for language in LANGUAGES:
            self.assertIn("start", DEFAULTS[language])
            self.assertIn(language, PACKAGERS)

    def test_go_package_builds_bootstrap(self):
        if not shutil.which("go"):
            self.skipTest("go not installed")

        (self.root / "platform.toml").write_text('[project]\nlanguage = "go"\n')
        (self.root / "go.mod").write_text("module example.com/app\n\ngo 1.22\n")
        main = self.root / "cmd" / "server"
        main.mkdir(parents=True)
        (main / "main.go").write_text("package main\n\nfunc main() {}\n")

        package(self.root, self.root / "out")

        self.assertTrue((self.root / "out" / "bootstrap").exists())
