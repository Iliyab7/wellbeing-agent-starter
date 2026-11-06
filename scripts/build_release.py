"""Build a deterministic, public-only release. Run from any working directory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "README.md", "README.en.md", "START-HERE.md", "CHAT-STARTER.md", "AGENTS.md",
    "CHANGELOG.md", "VERSION", "pyproject.toml", ".gitignore", ".gitattributes",
}
PUBLIC_DIRS = {"agents", "skills", "adapters", "prompts", "templates", "docs", "wellbeing",
               "tests", "examples", "schemas", "scripts", "qa", ".github", ".second-brain"}
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", ".venv", "private", "state", "sessions", "exports"}


def release_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            continue
        if not (str(rel) in ROOT_FILES or (len(rel.parts) > 1 and rel.parts[0] in PUBLIC_DIRS)):
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in release: {rel}")
        if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
            files.append(path)
    return sorted(files)


def main() -> None:
    version = (ROOT / "VERSION").read_text().strip()
    if not version or any(c not in "0123456789.-abcdefghijklmnopqrstuvwxyz" for c in version):
        raise ValueError("Unsafe version")
    files = release_files()
    manifest = {
        "schema_version": 1, "version": version,
        "source_revision": "e43881ec638d7d01afbe4a609954577f187b1558",
        "files": [{"path": p.relative_to(ROOT).as_posix(),
                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
    }
    manifest_path = ROOT / "package-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / f"wellbeing-agent-starter-v{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(files + [manifest_path]):
            name = f"wellbeing-agent-starter/{path.relative_to(ROOT).as_posix()}"
            info = zipfile.ZipInfo(name, (2026, 11, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "sha256": digest, "files": len(files) + 1}, indent=2))


if __name__ == "__main__":
    main()
