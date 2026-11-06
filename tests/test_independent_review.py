"""Independent adversarial regressions using only synthetic participant records."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wellbeing import core


NOW = datetime(2026, 11, 7, 9, 0, tzinfo=timezone.utc)


def policy():
    return {
        "purpose": "synthetic independent review", "retention_days": 14,
        "valid_until": None, "journal": True,
        "team_recipients": ["chief_of_staff", "manager", "analyst", "coach"],
        "sources": [{"id": "manual", "metrics": {"sleep": "hours"},
                     "analyze": True, "recipients": ["analyst"]}],
        "authority": {"draft_plans": True, "create_subagents": False},
        "attention": {"mode": "on_request", "quiet_start": None, "quiet_end": None,
                      "max_daily": None},
    }


def configured(p=None):
    state = core.initialize("Understand synthetic observations", "UTC", now=NOW)
    core.configure(state, p or policy(), confirmed=True, now=NOW)
    return state


def record(rid="one", value=8, hours_ago=1):
    return {"id": rid, "source": "manual", "metric": "sleep", "value": value,
            "unit": "hours", "observed_at": (NOW - timedelta(hours=hours_ago)).isoformat(),
            "origin": "synthetic"}


class IndependentRegressionTests(unittest.TestCase):
    def test_changed_unit_cannot_relabel_existing_numbers(self):
        state = configured()
        core.import_records(state, [record()], now=NOW)
        plan = core.create_plan(state, "Synthetic proposal", ["one"], now=NOW)
        updated = policy()
        updated["sources"][0]["metrics"]["sleep"] = "minutes"
        core.configure(state, updated, confirmed=True, now=NOW)
        observation = core.analyze(state, "manual", "sleep", now=NOW)
        self.assertEqual(observation["observations"]["numeric_count"], 0)
        self.assertFalse(any(p["id"] == plan["id"] for p in state["plans"]))

    def test_finite_values_cannot_make_non_json_mean(self):
        state = configured()
        core.import_records(state, [record("large-one", 1e308, 1),
                                    record("large-two", 1e308, 2)], now=NOW)
        result = core.analyze(state, "manual", "sleep", now=NOW)
        self.assertEqual(result["observations"]["mean_of_recorded_values"], 1e308)
        json.dumps(result, allow_nan=False)

    def test_invalid_tail_never_partially_imports(self):
        for invalid in (True, float("nan"), float("inf")):
            with self.subTest(value=repr(invalid)):
                state = configured()
                with self.assertRaises(core.PilotError):
                    core.import_records(state, [record("good", 8), record("bad", invalid, 2)], now=NOW)
                self.assertEqual(state["records"], [])

    def test_same_instant_different_offset_is_duplicate(self):
        state = configured()
        first = record()
        core.import_records(state, [first], now=NOW)
        repeated = copy.deepcopy(first)
        repeated["observed_at"] = datetime.fromisoformat(first["observed_at"]).astimezone(
            timezone(timedelta(hours=3, minutes=30))).isoformat()
        result = core.import_records(state, [repeated], now=NOW)
        self.assertEqual(result["duplicates_skipped"], 1)
        self.assertEqual(len(state["records"]), 1)

    def test_source_and_team_recipient_grants_are_both_required(self):
        state = configured()
        core.import_records(state, [record()], now=NOW)
        with self.assertRaises(core.PilotError):
            core.packet(state, "coach", "Read synthetic data", "manual", "sleep", now=NOW)
        p = policy()
        p["team_recipients"] = ["manager"]
        core.configure(state, p, confirmed=True, now=NOW)
        with self.assertRaises(core.PilotError):
            core.packet(state, "analyst", "Read synthetic data", "manual", "sleep", now=NOW)

    def test_revoke_invalidates_packets_and_dependent_plans(self):
        state = configured()
        core.import_records(state, [record()], now=NOW)
        packet = core.packet(state, "analyst", "Read synthetic data", "manual", "sleep", now=NOW)
        core.create_plan(state, "Synthetic proposal", ["one"], now=NOW)
        core.revoke(state, "manual", now=NOW)
        self.assertEqual(state["records"], [])
        self.assertEqual(state["plans"], [])
        with self.assertRaises(core.PilotError):
            core.verify_packet(state, packet, now=NOW)

    def test_policy_update_does_not_resume_paused_processing(self):
        state = configured()
        core.pause(state, now=NOW)
        core.configure(state, policy(), confirmed=True, now=NOW)
        self.assertEqual(state["status"], "paused")
        with self.assertRaises(core.PilotError):
            core.import_records(state, [record()], now=NOW)
        with self.assertRaises(core.PilotError):
            core.packet(state, "manager", "Synthetic task", now=NOW)

    def test_expiry_blocks_data_use_and_packet_forwarding(self):
        p = policy()
        p["valid_until"] = (NOW + timedelta(hours=1)).isoformat()
        state = configured(p)
        core.import_records(state, [record()], now=NOW)
        packet = core.packet(state, "analyst", "Synthetic task", "manual", "sleep", now=NOW)
        later = NOW + timedelta(hours=2)
        with self.assertRaises(core.PilotError):
            core.analyze(state, "manual", "sleep", now=later)
        with self.assertRaises(core.PilotError):
            core.verify_packet(state, packet, now=later)

    def test_export_refuses_repo_or_existing_target(self):
        state = configured()
        with self.assertRaises(core.PilotError):
            core.export_state(state, core.ROOT / "participant-private.json", confirmed=True)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "existing.json"
            target.write_text("keep", encoding="utf-8")
            with self.assertRaises(core.PilotError):
                core.export_state(state, target, confirmed=True)
            self.assertEqual(target.read_text(), "keep")

    def test_improvement_does_not_imply_execution_or_adoption(self):
        state = configured()
        item = core.create_plan(state, "Synthetic proposal", now=NOW)
        changed = core.review_plan(state, item["id"], outcome="Synthetic self-report of improvement", now=NOW)
        self.assertEqual(changed["implementation"], "unknown")
        self.assertEqual(changed["decision"], "proposed")
        self.assertEqual(changed["receipt"], "not_delivered")
        self.assertEqual(changed["outcome"]["causality"], "not_established")

    def test_correction_invalidates_packet_and_pauses_dependent_plan(self):
        state = configured()
        core.import_records(state, [record()], now=NOW)
        plan = core.create_plan(state, "Synthetic proposal", ["one"], now=NOW)
        packet = core.packet(state, "analyst", "Synthetic task", "manual", "sleep", now=NOW)
        changed = record(value=7)
        core.correct_record(state, changed, confirmed=True, now=NOW)
        self.assertEqual(state["records"][0]["value"], 7)
        self.assertEqual(next(p for p in state["plans"] if p["id"] == plan["id"])["decision"], "paused")
        with self.assertRaises(core.PilotError):
            core.verify_packet(state, packet, now=NOW)

    def test_correction_collision_is_not_silent_record_deletion(self):
        state = configured()
        core.import_records(state, [record("a", 8, 1), record("b", 8, 2)], now=NOW)
        before = copy.deepcopy(state)
        with self.assertRaises(core.PilotError):
            core.correct_record(state, record("a", 8, 2), confirmed=True, now=NOW)
        self.assertEqual(state, before)

    def test_malformed_state_returns_structured_error_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            original = '{"schema_version": 1}'
            path.write_text(original, encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "wellbeing", "--home", directory, "status"],
                                    cwd=core.ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(json.loads(result.stderr)["ok"])
            self.assertEqual(path.read_text(), original)

    def test_cli_persisted_lifecycle_and_revoked_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "workspace"

            def call(*args, expected=0):
                result = subprocess.run([sys.executable, "-m", "wellbeing", "--home", str(home), *args],
                                        cwd=core.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                return json.loads(result.stdout if expected == 0 else result.stderr)

            call("init", "--goal", "Synthetic CLI review", "--timezone", "UTC")
            p = base / "policy.json"
            p.write_text(json.dumps(policy()), encoding="utf-8")
            call("configure", "--file", str(p), "--confirmed")
            data = record()
            data["observed_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            records = base / "records.json"
            records.write_text(json.dumps([data]), encoding="utf-8")
            call("import", "--file", str(records))
            out = base / "packet.json"
            call("packet", "--role", "analyst", "--task", "Synthetic data question",
                 "--source", "manual", "--metric", "sleep", "--output", str(out))
            self.assertTrue(call("verify-packet", "--file", str(out))["result"]["valid"])
            call("pause")
            call("analyze", "--source", "manual", "--metric", "sleep", expected=2)
            call("resume", "--confirmed")
            call("revoke", "--source", "manual")
            call("verify-packet", "--file", str(out), expected=2)
            self.assertEqual(call("status")["result"]["records"], 0)
            export = base / "export.json"
            call("export", "--file", str(export), "--confirmed")
            self.assertTrue(export.exists())
            call("delete", "--confirmed")
            self.assertFalse((home / "state.json").exists())
            self.assertTrue(export.exists(), "Delete must not claim removal of a separately exported copy")


if __name__ == "__main__":
    unittest.main()
