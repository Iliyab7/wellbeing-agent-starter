"""Build a deterministic public-only release from any working directory.

source_revision identifies the input code commit, not a later metadata commit.
Use --source-revision for controlled composition or an extracted source archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "README.md", "README.en.md", "START-HERE.md", "CHAT-STARTER.md", "AGENTS.md",
    "CHANGELOG.md", "VERSION", "pyproject.toml", ".gitignore", ".gitattributes",
    "INSTALL.md", "INSTALL-HTTP.md", "PHONE-SETUP.md", "WORK-PLAN.md", "requirements-mvp.txt", "Dockerfile",
    "compose.yaml", "plugin.json", "LICENSE", "LICENSE.md", "LICENSE.txt",
}
PUBLIC_DIRS = {"agents", "skills", "adapters", "prompts", "templates", "docs", "wellbeing",
               "tests", "examples", "schemas", "scripts", "qa", ".github", ".second-brain"}
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv",
                 "private", "state", "sessions", "exports", "source-review", "meetings", "history"}
REVISION = re.compile(r"[0-9a-f]{40}")


def release_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS or part.endswith(".egg-info") for part in rel.parts):
            continue
        if not (rel.as_posix() in ROOT_FILES or (len(rel.parts) > 1 and rel.parts[0] in PUBLIC_DIRS)):
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in release: {rel.as_posix()}")
        if path.is_file() and path.suffix not in {".pyc", ".pyo"} and path.name != ".DS_Store":
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def source_revision(supplied: str | None = None) -> str:
    if supplied is not None:
        if not REVISION.fullmatch(supplied):
            raise ValueError("--source-revision must be a lowercase 40-character Git commit ID")
        return supplied
    # Do not accidentally identify an unrelated enclosing checkout.
    try:
        top = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if Path(top).resolve() == ROOT.resolve():
            value = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD^{commit}"],
                check=True, capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if REVISION.fullmatch(value):
                return value
    except (OSError, subprocess.SubprocessError):
        pass
    # An extracted release can retain the original input provenance. This does
    # not assert that changed archive files were tested at that commit.
    try:
        manifest = json.loads((ROOT / "package-manifest.json").read_text(encoding="utf-8"))
        value = manifest.get("source_revision") if isinstance(manifest, dict) else None
        if isinstance(value, str) and REVISION.fullmatch(value):
            return value
    except (OSError, UnicodeError, ValueError):
        pass
    raise ValueError("Input revision unavailable; supply --source-revision with the exact input code commit")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", help="Exact input code commit; may precede the release metadata commit")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version or any(c not in "0123456789.-abcdefghijklmnopqrstuvwxyz" for c in version):
        raise ValueError("Unsafe version")
    revision = source_revision(args.source_revision)
    files = release_files()
    manifest = {
        "schema_version": 1, "version": version,
        "source_revision": revision,
        "files": [{"path": p.relative_to(ROOT).as_posix(),
                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
    }
    manifest_path = ROOT / "package-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / f"wellbeing-agent-starter-v{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(files + [manifest_path], key=lambda p: p.relative_to(ROOT).as_posix()):
            name = f"wellbeing-agent-starter/{path.relative_to(ROOT).as_posix()}"
            info = zipfile.ZipInfo(name, (2026, 11, 7, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "sha256": digest, "files": len(files) + 1,
                      "source_revision": revision, "source_revision_meaning": "input_code_commit"}, indent=2))


if __name__ == "__main__":
    main()
