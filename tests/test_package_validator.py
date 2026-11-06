"""Deliberate package failure fixtures; all tokens and records are synthetic."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "validate_package.py"
SPEC = importlib.util.spec_from_file_location("package_validator", MODULE)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "VERSION").write_text("0.1.0\n")
        (self.root / "README.md").write_text("# Synthetic fixture\n", encoding="utf-8")

    def manifest(self):
        paths = sorted(path for path in self.root.rglob("*") if path.is_file() and path.name != validator.MANIFEST)
        value = {
            "schema_version": 1, "version": "0.1.0", "source_revision": "a" * 40,
            "files": [{"path": path.relative_to(self.root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths],
        }
        (self.root / validator.MANIFEST).write_text(json.dumps(value), encoding="utf-8")
        return value

    def codes(self):
        report = validator.validate(self.root, check_required=False)
        return {item["code"] for item in report["findings"]}

    def test_clean_fixture(self):
        self.manifest()
        self.assertEqual(set(), self.codes())

    def test_tampering_detected(self):
        self.manifest()
        (self.root / "README.md").write_text("Changed after release", encoding="utf-8")
        self.assertIn("integrity-mismatch", self.codes())

    def test_unlisted_file_detected(self):
        self.manifest()
        (self.root / "extra.md").write_text("Unreviewed", encoding="utf-8")
        self.assertIn("unlisted-file", self.codes())

    def test_traversal_manifest_rejected(self):
        value = self.manifest()
        value["files"].append({"path": "../outside.txt", "sha256": "0" * 64})
        (self.root / validator.MANIFEST).write_text(json.dumps(value))
        self.assertIn("manifest-path", self.codes())

    def test_credential_match_reports_no_secret(self):
        # Construct a fake pattern match; no usable credential is stored in the repository.
        fake = "ghp" + "_" + "Z" * 36
        (self.root / "example.txt").write_text(fake)
        self.manifest()
        report = validator.validate(self.root, check_required=False)
        self.assertIn("credential-pattern", {item["code"] for item in report["findings"]})
        self.assertNotIn(fake, json.dumps(report))

    def test_private_state_and_environment_files_rejected(self):
        (self.root / "state").mkdir()
        (self.root / "state" / "data.json").write_text("{}")
        (self.root / ".env").write_text("EXAMPLE=placeholder\n")
        self.manifest()
        self.assertTrue({"private-path", "environment-file"}.issubset(self.codes()))

    def test_link_must_stay_inside_package_and_exist(self):
        (self.root / "README.md").write_text("[missing](missing.md)\n[escape](../outside.md)\n")
        self.manifest()
        self.assertTrue({"broken-link", "outside-link"}.issubset(self.codes()))

    def test_duplicate_json_keys_rejected(self):
        (self.root / "example.json").write_text('{"mode": "ask", "mode": "send"}')
        self.manifest()
        self.assertIn("json-invalid", self.codes())

    def test_skill_frontmatter_required(self):
        folder = self.root / "skills" / "sample"
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("---\nname: sample\n---\nUseful instructions.\n")
        self.manifest()
        self.assertIn("skill-metadata", self.codes())

    def test_registry_instruction_references_must_exist(self):
        (self.root / "agents").mkdir()
        catalog = {"interface": {"id": "host", "instructions": "agents/missing.md", "skills": []}, "team": []}
        (self.root / "agents" / "registry.json").write_text(json.dumps(catalog))
        self.manifest()
        self.assertIn("registry-target", self.codes())

    def test_registry_cannot_escape_package(self):
        (self.root / "agents").mkdir()
        catalog = {"interface": {"id": "host", "instructions": "../outside.md", "skills": []}, "team": []}
        (self.root / "agents" / "registry.json").write_text(json.dumps(catalog))
        self.manifest()
        self.assertIn("registry-path", self.codes())

    def test_blueprint_requires_role_scope_and_reporting(self):
        (self.root / "agents").mkdir()
        blueprint = {"schema_version": 1, "roles": [{"id": "manager", "mission": "Coordinate this trial"}]}
        (self.root / "agents" / "team-blueprint.json").write_text(json.dumps(blueprint))
        self.manifest()
        self.assertTrue({"blueprint-contract", "blueprint-permissions", "blueprint-reporting"}.issubset(self.codes()))

    def test_symlink_rejected(self):
        link = self.root / "copy.md"
        try:
            link.symlink_to(self.root / "README.md")
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this platform")
        self.manifest()
        self.assertIn("symlink", self.codes())


if __name__ == "__main__":
    unittest.main()
