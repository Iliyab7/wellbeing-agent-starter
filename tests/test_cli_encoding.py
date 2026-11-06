"""The CLI must not report failure after committing Persian data on Windows/ASCII pipes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliEncodingTests(unittest.TestCase):
    def command(self, home, *arguments):
        environment = dict(os.environ, PYTHONIOENCODING="ascii")
        return subprocess.run(
            [sys.executable, "-m", "wellbeing", "--home", str(home), *arguments],
            cwd=ROOT, env=environment, capture_output=True,
        )

    def test_persian_success_is_json_and_commits_exactly_once_with_ascii_pipe(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "private-participant"
            initialized = self.command(home, "init", "--goal", "هدف ساختگی فارسی", "--timezone", "UTC")
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            configured = self.command(home, "configure", "--file", str(ROOT / "examples/policy.synthetic.json"), "--confirmed")
            self.assertEqual(0, configured.returncode, configured.stderr)
            result = self.command(home, "plan", "--text", "آزمون ساختگی فارسی")
            self.assertEqual(0, result.returncode, result.stderr)
            decoded = json.loads(result.stdout.decode("ascii"))
            self.assertTrue(decoded["ok"])
            self.assertEqual("آزمون ساختگی فارسی", decoded["result"]["text"])
            state = json.loads((home / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(1, len(state["plans"]))
            self.assertEqual(decoded["result"]["id"], state["plans"][0]["id"])

    def test_unicode_error_is_valid_json_with_ascii_pipe(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "پوشه-ساختگی"
            home.write_text("synthetic file blocks a workspace directory", encoding="utf-8")
            result = self.command(home, "status")
            self.assertEqual(2, result.returncode, result.stderr)
            decoded = json.loads(result.stderr.decode("ascii"))
            self.assertFalse(decoded["ok"])
            self.assertIn("پوشه-ساختگی", decoded["error"])
            self.assertEqual(b"", result.stdout)


if __name__ == "__main__":
    unittest.main()
