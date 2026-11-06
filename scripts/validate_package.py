"""Validate the public release without dependencies, network access or private input.

This is a package integrity guard, not a medical validator or comprehensive DLP.
The report never includes a matched credential or participant record.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "package-manifest.json"
REQUIRED = (
    "README.md", "README.en.md", "AGENTS.md", "START-HERE.md", "CHAT-STARTER.md",
    "VERSION", "pyproject.toml", "docs/architecture.md", "docs/harvey-handoff.md",
    "docs/acceptance-tests.md", "docs/privacy-and-safety.md", "docs/runtime.md",
    "docs/participant-pilot-fa.md", "docs/source-analysis.md",
    "docs/requirements-traceability.md", "docs/orchestration-playbook-fa.md",
    "agents/registry.json", "agents/team-blueprint.json",
    "agents/chief-of-staff.md", "agents/manager.md", "agents/analyst.md", "agents/coach.md",
    "adapters/host-capabilities.md", "adapters/dot.md", "adapters/grok.md",
    "templates/participant-charter.md", "templates/private-session.md",
    "templates/test-feedback.md", "templates/task-contract.json", "templates/task-report.json",
    "templates/agent-instance-registry.json", "scripts/demo.py", "scripts/build_release.py",
    "scripts/validate_package.py", ".github/workflows/ci.yml",
    "wellbeing/__main__.py", "wellbeing/core.py", "wellbeing/cli.py", "wellbeing/tasks.py",
    "schemas/task-contract.schema.json", "schemas/task-report.schema.json",
    "examples/task.synthetic.json", "examples/task-report.synthetic.json",
)
SKILLS = ("wellbeing-intake", "wellbeing-orchestrate", "wellbeing-analyze", "wellbeing-coach", "wellbeing-review",
          "wellbeing-host-operations", "wellbeing-domain-context")
IGNORED_DIRS = {".git", "dist", "build", "__pycache__", ".pytest_cache", ".venv", "venv", ".mypy_cache"}
PRIVATE_DIRS = {"private", "state", "sessions", "exports", ".wellbeing", "source-review", "meetings", "history"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".csv", ".html", ".svg", ".mmd"}
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("provider-api-key", re.compile(r"\bsk-(?:proj-|ant-api\d+-)?[A-Za-z0-9_-]{32,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
)
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\s*\)")


def fail(findings: list[dict], code: str, path: str, detail: str) -> None:
    findings.append({"code": code, "path": path, "detail": detail})


def safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in value.split("/")) and ":" not in value


def duplicate_free_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(text: str) -> object:
    return json.loads(text, object_pairs_hook=duplicate_free_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON number")))


def public_files(root: Path, findings: list[dict]) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in IGNORED_DIRS or part.endswith(".egg-info") for part in rel.parts):
            continue
        if path.is_symlink():
            fail(findings, "symlink", rel.as_posix(), "Symlinks are not allowed in a public release.")
            continue
        if not path.is_file() or path.suffix in {".pyc", ".pyo"} or path.name == ".DS_Store":
            continue
        if any(part in PRIVATE_DIRS for part in rel.parts) or path.name.endswith(".private.json"):
            fail(findings, "private-path", rel.as_posix(), "Private/source-history artifacts must stay outside this package.")
        if (path.name == ".env" or path.name.startswith(".env.")) and path.name != ".env.example":
            fail(findings, "environment-file", rel.as_posix(), "A real environment file must not be released.")
        if path.suffix in {".db", ".sqlite", ".sqlite3", ".pem", ".key"}:
            fail(findings, "sensitive-file", rel.as_posix(), "Database/key artifacts are not part of the pilot release.")
        files.append(path)
    return files


def validate_manifest(root: Path, files: list[Path], findings: list[dict]) -> None:
    path = root / MANIFEST
    if not path.is_file():
        fail(findings, "manifest-missing", MANIFEST, "Run scripts/build_release.py after completing release files.")
        return
    try:
        manifest = parse_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        fail(findings, "manifest-json", MANIFEST, type(exc).__name__)
        return
    if not isinstance(manifest, dict):
        fail(findings, "manifest-shape", MANIFEST, "Expected a JSON object.")
        return
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
        fail(findings, "manifest-shape", MANIFEST, "Expected schema_version=1 and a files array.")
        return
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("source_revision", ""))):
        fail(findings, "source-revision", MANIFEST, "Expected the exact 40-character source commit revision.")
    version_file = root / "VERSION"
    if version_file.is_file() and manifest.get("version") != version_file.read_text(encoding="utf-8").strip():
        fail(findings, "version-mismatch", MANIFEST, "Manifest and VERSION differ.")
    listed: set[str] = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or not safe_path(entry.get("path")):
            fail(findings, "manifest-path", MANIFEST, "A file entry has an unsafe or missing relative path.")
            continue
        name = entry["path"]
        if name in listed or name == MANIFEST:
            fail(findings, "manifest-duplicate", MANIFEST, "Duplicate path or a self-referential manifest entry.")
            continue
        listed.add(name)
        expected = entry.get("sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            fail(findings, "manifest-hash", name, "Expected a SHA-256 hex digest.")
            continue
        target = root / name
        if not target.resolve().is_relative_to(root.resolve()):
            fail(findings, "manifest-path", name, "Resolved manifest path leaves the package.")
            continue
        if not target.is_file() or target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent.is_relative_to(root)):
            fail(findings, "manifest-file-missing", name, "Manifest entry is not a regular package file.")
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            fail(findings, "integrity-mismatch", name, "File bytes do not match the release manifest.")
    actual = {path.relative_to(root).as_posix() for path in files if path.relative_to(root).as_posix() != MANIFEST}
    for name in sorted(actual - listed):
        fail(findings, "unlisted-file", name, "File is absent from the public release manifest.")
    for name in sorted(listed - actual):
        fail(findings, "nonrelease-entry", name, "Manifest entry is outside the validated release files.")


def validate_links(root: Path, path: Path, text: str, findings: list[dict]) -> None:
    # Fenced examples can contain illustrative paths. Real prose links are checked.
    prose = re.sub(r"(?ms)^(```|~~~).*?^\1\s*$", "", text)
    rel = path.relative_to(root).as_posix()
    for match in LINK.finditer(prose):
        destination = match.group(1).strip("<>")
        if destination.startswith("#"):
            continue
        try:
            parsed = urlsplit(destination)
        except ValueError:
            fail(findings, "unsafe-link", rel, "Invalid link URL.")
            continue
        if parsed.scheme or parsed.netloc:
            continue
        raw = unquote(parsed.path)
        if not raw:
            continue
        if "\x00" in raw or "\\" in raw:
            fail(findings, "unsafe-link", rel, "Invalid local link path.")
            continue
        target = (path.parent / raw).resolve()
        if not target.is_relative_to(root.resolve()):
            fail(findings, "outside-link", rel, "A local link leaves the release package.")
        elif not target.exists():
            fail(findings, "broken-link", rel, f"Missing local link target: {raw}")


def validate_skill(path: Path, root: Path, text: str, findings: list[dict]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(findings, "skill-frontmatter", rel, "SKILL.md must start with YAML frontmatter.")
        return
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        fail(findings, "skill-frontmatter", rel, "Unclosed frontmatter.")
        return
    front = "\n".join(lines[1:end])
    for key in ("name", "description"):
        match = re.search(r"(?m)^" + key + r":\s*(.+)$", front)
        if not match or match.group(1).strip().strip("\"'") in {"", "|", ">"}:
            fail(findings, "skill-metadata", rel, f"Missing nonempty inline {key}.")
    name = re.search(r"(?m)^name:\s*([^\n]+)$", front)
    if name and name.group(1).strip().strip("\"'") != path.parent.name:
        fail(findings, "skill-name", rel, "Skill name must match its directory.")
    if not "\n".join(lines[end + 1:]).strip():
        fail(findings, "skill-body", rel, "Skill has no instructions.")


def validate_registry(root: Path, findings: list[dict]) -> None:
    relative = "agents/registry.json"
    path = root / relative
    if not path.is_file():
        return  # The required-file check owns missing entry points.
    try:
        data = parse_json(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("team"), list) or not isinstance(data.get("interface"), dict):
            raise ValueError("Invalid role catalog")
        roles = [data["interface"], *data["team"]]
        seen = set()
        for role in roles:
            if not isinstance(role, dict) or not isinstance(role.get("id"), str) or not role["id"] or role["id"] in seen:
                raise ValueError("Invalid or duplicate role")
            seen.add(role["id"])
            if not isinstance(role.get("skills"), list):
                raise ValueError("Missing role skills list")
            for target in [role.get("instructions"), *role["skills"]]:
                if not safe_path(target):
                    fail(findings, "registry-path", relative, "Role instructions/skills must use safe package-relative paths.")
                elif not (root / target).is_file():
                    fail(findings, "registry-target", relative, f"Missing role instruction/skill: {target}")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        fail(findings, "registry-shape", relative, "Expected a valid role catalog with unique role IDs and skill references.")


def validate_blueprint(root: Path, findings: list[dict]) -> None:
    relative = "agents/team-blueprint.json"
    path = root / relative
    if not path.is_file():
        return
    try:
        data = parse_json(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("roles"), list) or not data["roles"]:
            raise ValueError("Invalid blueprint")
        ids = set()
        for role in data["roles"]:
            if not isinstance(role, dict) or not isinstance(role.get("id"), str) or role["id"] in ids:
                raise ValueError("Invalid role")
            ids.add(role["id"])
            if not isinstance(role.get("mission"), str) or not role["mission"].strip():
                fail(findings, "blueprint-mission", relative, "Each role needs a nonempty mission.")
            for key in ("objectives", "responsibilities", "inputs", "outputs", "skills"):
                if not isinstance(role.get(key), list) or not role[key]:
                    fail(findings, "blueprint-contract", relative, f"Each role needs a nonempty {key} array.")
            permissions = role.get("permissions")
            if not isinstance(permissions, dict) or not all(isinstance(permissions.get(key), list) for key in ("may", "may_not", "requires_current_scope")):
                fail(findings, "blueprint-permissions", relative, "Each role needs may, may_not and requires_current_scope lists.")
            reporting = role.get("reporting")
            if not isinstance(reporting, dict) or not all(reporting.get(key) for key in ("to", "when", "completion")):
                fail(findings, "blueprint-reporting", relative, "Each role needs a reporting recipient, trigger and completion contract.")
            references = role.get("skills", [])
            if not isinstance(references, list):
                references = []
            if "instructions" in role:
                references = [role["instructions"], *references]
            for target in references:
                if not safe_path(target):
                    fail(findings, "blueprint-path", relative, "Unsafe blueprint instruction/skill path.")
                elif not (root / target).is_file():
                    fail(findings, "blueprint-target", relative, f"Missing blueprint instruction/skill: {target}")
        registry_path = root / "agents/registry.json"
        if registry_path.is_file():
            registry = parse_json(registry_path.read_text(encoding="utf-8"))
            expected = {registry["interface"]["id"], *(role["id"] for role in registry["team"])}
            if ids != expected:
                fail(findings, "blueprint-role-mismatch", relative, "Blueprint and role catalog IDs differ.")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        fail(findings, "blueprint-shape", relative, "Expected a complete versioned blueprint with unique role IDs.")


def validate(root: Path, *, check_manifest: bool = True, check_required: bool = True) -> dict:
    findings: list[dict] = []
    files = public_files(root, findings)
    if check_required:
        for name in REQUIRED + tuple(f"skills/{name}/SKILL.md" for name in SKILLS):
            if not (root / name).is_file():
                fail(findings, "required-file", name, "Missing required pilot entry point.")
        if not list((root / "tests").glob("test_*.py")):
            fail(findings, "tests-missing", "tests", "No discoverable unit tests.")
    checked_text = 0
    for path in files:
        if path.suffix not in TEXT_SUFFIXES and path.name not in {"VERSION", ".gitignore", ".gitattributes", "LICENSE"}:
            continue
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            fail(findings, "text-encoding", rel, "Expected readable UTF-8 text.")
            continue
        checked_text += 1
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(findings, "credential-pattern", rel, f"Possible {label}; inspect privately, never print its value.")
        if path.suffix == ".json":
            try:
                parse_json(text)
            except (ValueError, TypeError):
                fail(findings, "json-invalid", rel, "Invalid JSON, duplicate key or nonfinite number.")
        elif path.suffix == ".py":
            try:
                ast.parse(text, filename=rel)
            except SyntaxError as exc:
                fail(findings, "python-syntax", rel, f"Syntax error on line {exc.lineno}.")
        elif path.suffix == ".md":
            validate_links(root, path, text, findings)
            if path.name == "SKILL.md":
                validate_skill(path, root, text, findings)
    validate_registry(root, findings)
    validate_blueprint(root, findings)
    if check_manifest:
        validate_manifest(root, files, findings)
    return {
        "status": "passed" if not findings else "failed",
        "scope": "public-package-structure-and-integrity" if check_manifest else "public-package-structure-only",
        "manifest_checked": check_manifest,
        "files_checked": len(files), "text_files_checked": checked_text,
        "findings": findings,
        "limits": ["No live host, wearable or external-action test.", "Credential patterns do not replace a human privacy review.", "File hashes do not authenticate the publisher."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--skip-manifest", action="store_true", help="Development-only structure check; not release verification.")
    args = parser.parse_args()
    report = validate(args.root.resolve(), check_manifest=not args.skip_manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
