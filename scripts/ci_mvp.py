"""Run the local synthetic MVP release checks with installed optional dependencies.

This does not install packages, deploy, access accounts or claim live acceptance.
Commands inherit the terminal so unittest failures and skips remain visible.
"""
from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def dependency_errors() -> list[str]:
    errors = []
    for line in (ROOT / "requirements-mvp.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            errors.append("Unsupported dependency declaration; exact package==version required")
            continue
        name, expected = line.split("==")
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            errors.append(f"Missing optional dependency: {name}")
            continue
        if installed != expected:
            errors.append(f"Dependency version mismatch: {name}; expected {expected}, found {installed}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", help="Exact input code commit passed to the release builder")
    args = parser.parse_args()
    errors = dependency_errors()
    if errors:
        print(json.dumps({"status": "failed", "phase": "dependencies", "errors": errors,
                          "next": "python -m pip install -r requirements-mvp.txt"}, indent=2), flush=True)
        return 1
    build = ["scripts/build_release.py"]
    if args.source_revision is not None:
        build += ["--source-revision", args.source_revision]
    commands = [
        ["-m", "unittest", "discover", "-s", "tests", "-v"],
        ["scripts/demo.py"],
        ["scripts/mvp_smoke.py"],
        build,
        ["scripts/validate_package.py"],
    ]
    results = []
    for command in commands:
        print(json.dumps({"running": ["python", *command]}), flush=True)
        try:
            completed = subprocess.run([sys.executable, *command], cwd=ROOT, check=False)
            code = completed.returncode
        except OSError:
            code = 1
        except KeyboardInterrupt:
            print(json.dumps({"status": "interrupted", "completed_checks": results}), flush=True)
            return 130
        results.append({"command": ["python", *command], "exit_code": code})
        if code:
            print(json.dumps({"status": "failed", "checks": results,
                              "remaining_checks": "not_run_after_failure"}, indent=2), flush=True)
            return 1
    print(json.dumps({"status": "passed", "scope": "local_synthetic_release_checks",
                      "checks": results,
                      "skips": "Inspect unittest output; exit code zero does not mean zero skips.",
                      "limits": "No real phone, Dot, channel, public deployment, Docker or OpenGym-server acceptance."}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
