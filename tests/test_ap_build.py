import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ap_build import VERBS, command, main  # noqa: E402


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

    def test_package_runs_the_sam_recipe_into_the_artifacts_dir(self):
        self.write('[project]\nlanguage = "go"\n')
        (self.root / "Makefile").write_text(
            'build-ApiFunction:\n\techo built > "$(ARTIFACTS_DIR)/bootstrap"\n'
        )
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)

        self.assertEqual(main(["package"]), 0)
        self.assertEqual(
            (self.root / ".ap-build" / "package" / "bootstrap").read_text().strip(),
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
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("ap-build test: exit 3", result.stdout)
