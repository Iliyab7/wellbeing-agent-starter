"""Behavior checks for the local pilot, using only synthetic participants."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from wellbeing import core

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2030, 1, 8, 12, 0, tzinfo=timezone.utc)


def policy():
    return core.read_json(ROOT / "examples" / "policy.synthetic.json")


def participant():
    state = core.initialize("Synthetic goal", "UTC", now=NOW)
    core.configure(state, policy(), confirmed=True, now=NOW)
    return state


def record(identifier="r1", value=7, days=1):
    return {"id": identifier, "source": "manual", "metric": "sleep_hours", "value": value,
            "unit": "hours", "observed_at": core.stamp(NOW-timedelta(days=days)), "origin": "synthetic"}


class ConsentTests(unittest.TestCase):
    def test_init_has_no_implicit_consent(self):
        state = core.initialize("Synthetic goal", "UTC", now=NOW)
        self.assertEqual("awaiting_consent", state["status"])
        with self.assertRaises(core.PilotError):
            core.import_records(state, [record()], NOW)
        with self.assertRaises(core.PilotError):
            core.configure(state, policy(), now=NOW)

    def test_no_recipient_grants_by_default(self):
        state = participant()
        p = policy()
        p["team_recipients"] = []
        core.configure(state, p, True, NOW)
        with self.assertRaises(core.PilotError):
            core.packet(state, "analyst", "Synthetic task", now=NOW)

    def test_collection_is_separate_from_analysis(self):
        state = participant()
        p = policy()
        p["sources"][0]["analyze"] = False
        core.configure(state, p, True, NOW)
        core.import_records(state, [record()], NOW)
        with self.assertRaises(core.PilotError):
            core.analyze(state, "manual", "sleep_hours", now=NOW)

    def test_native_team_authority_independent(self):
        state = participant()
        state["policy"]["authority"]["create_subagents"] = False
        self.assertEqual("manifest_only", core.team(state, "inline", NOW)["execution_status"])
        with self.assertRaises(core.PilotError):
            core.team(state, "native", NOW)

    def test_journal_can_be_declined_without_losing_analysis(self):
        state = participant()
        state["policy"]["journal"] = False
        core.import_records(state, [record()], NOW)
        self.assertEqual(1, core.analyze(state, "manual", "sleep_hours", now=NOW)["observations"]["numeric_count"])
        with self.assertRaises(core.PilotError):
            core.checkin(state, "Synthetic note", NOW)

    def test_changed_purpose_does_not_repurpose_existing_data(self):
        state = participant()
        core.import_records(state, [record()], NOW)
        core.checkin(state, "Synthetic note", NOW)
        p = policy()
        p["purpose"] = "A different participant-approved purpose"
        core.configure(state, p, True, NOW)
        self.assertEqual([], state["records"])
        self.assertEqual([], state["checkins"])

    def test_goal_change_invalidates_and_pauses_without_implied_new_consent(self):
        state = participant()
        plan = core.create_plan(state, "Synthetic experiment", now=NOW)
        packet = core.packet(state, "manager", "Synthetic task", now=NOW)
        core.set_goal(state, "Different synthetic goal", confirmed=True, now=NOW)
        self.assertEqual("awaiting_consent", state["status"])
        self.assertEqual("paused", state["plans"][0]["decision"])
        self.assertEqual(plan["id"], state["plans"][0]["id"])
        with self.assertRaises(core.PilotError):
            core.verify_packet(state, packet, NOW)

    def test_same_purpose_goal_change_does_not_resume_paused_workspace(self):
        state = participant()
        core.pause(state, NOW)
        core.set_goal(state, "Same-purpose refinement", True, True, NOW)
        self.assertEqual("paused", state["status"])


class ObservationTests(unittest.TestCase):
    def test_missing_is_not_zero_and_one_point_is_not_a_trend(self):
        state = participant()
        core.import_records(state, [record(), record("r2", None, 2)], NOW)
        result = core.analyze(state, "manual", "sleep_hours", now=NOW)
        self.assertEqual(7, result["observations"]["mean_of_recorded_values"])
        self.assertEqual(1, result["observations"]["explicit_missing_count"])
        self.assertEqual([], result["hypotheses"])
        self.assertEqual([], result["recommendations"])
        self.assertEqual([], result["confirmed_explanations"])

    def test_timestamp_requires_offset(self):
        state = participant()
        r = record()
        r["observed_at"] = "2030-01-07"
        with self.assertRaises(core.PilotError):
            core.import_records(state, [r], NOW)
        self.assertEqual([], state["records"])

    def test_expired_or_future_records_rejected(self):
        state = participant()
        for r in (record(days=31), record(days=-1)):
            with self.assertRaises(core.PilotError):
                core.import_records(state, [r], NOW)

    def test_boolean_is_not_numeric_observation(self):
        state = participant()
        with self.assertRaises(core.PilotError):
            core.import_records(state, [record(value=True)], NOW)

    def test_invalid_unit_rejects_whole_batch(self):
        state = participant()
        bad = record("bad", days=2)
        bad["unit"] = "minutes"
        with self.assertRaises(core.PilotError):
            core.import_records(state, [record(), bad], NOW)
        self.assertEqual([], state["records"])

    def test_all_source_availability_states_are_preserved(self):
        state = participant()
        for availability in ("absent", "partial", "stale", "conflicting", "technical_failure", "not_checked"):
            core.set_source_status(state, "manual", availability, NOW)
            result = core.analyze(state, "manual", "sleep_hours", now=NOW)
            self.assertEqual(availability, result["source_status"]["status"])
            self.assertIsNone(result["observations"]["mean_of_recorded_values"])

    def test_coverage_uses_participant_date(self):
        state = participant()
        state["profile"]["timezone"] = "UTC+03:30"
        r = record()
        r["observed_at"] = "2030-01-07T22:00:00+00:00"
        core.import_records(state, [r], NOW)
        result = core.analyze(state, "manual", "sleep_hours", "2030-01-08", "2030-01-08", NOW)
        self.assertEqual(1, result["observations"]["days_with_numeric_observations"])


class LifecycleTests(unittest.TestCase):
    def test_retention_removes_dependent_plan_and_blocks_old_packet(self):
        state = participant()
        p = policy()
        p["retention_days"] = 7
        core.configure(state, p, True, NOW)
        core.import_records(state, [record(days=5)], NOW)
        core.create_plan(state, "Synthetic experiment", ["r1"], NOW)
        packet = core.packet(state, "analyst", "Synthetic task", "manual", "sleep_hours", NOW)
        later = NOW + timedelta(days=3)
        core.prune(state, later)
        self.assertEqual([], state["records"])
        self.assertEqual([], state["plans"])
        with self.assertRaises(core.PilotError):
            core.verify_packet(state, packet, later)

    def test_journal_not_automatically_shared(self):
        state = participant()
        core.checkin(state, "Private synthetic journal text", NOW)
        packet = core.packet(state, "analyst", "Synthetic task", now=NOW)
        self.assertNotIn("Private synthetic journal text", json.dumps(packet))
        self.assertNotIn("checkins", packet["minimum_context"])

    def test_receipt_statuses_do_not_infer_implementation(self):
        state = participant()
        plan = core.create_plan(state, "Synthetic experiment", now=NOW)
        for receipt in ("withheld", "failed", "unknown", "delivered", "acknowledged"):
            result = core.review_plan(state, plan["id"], receipt=receipt, now=NOW)
            self.assertEqual("unknown", result["implementation"])
            self.assertIsNone(result["outcome"])

    def test_deleting_record_invalidates_derived_artifacts(self):
        state = participant()
        core.import_records(state, [record()], NOW)
        core.create_plan(state, "Synthetic experiment", ["r1"], NOW)
        packet = core.packet(state, "analyst", "Synthetic task", "manual", "sleep_hours", NOW)
        core.delete_record(state, "r1", True, NOW)
        self.assertEqual([], state["plans"])
        with self.assertRaises(core.PilotError):
            core.verify_packet(state, packet, NOW)


class StorageTests(unittest.TestCase):
    def test_same_alias_does_not_mix_workspaces(self):
        a = core.initialize("Synthetic A", "UTC", "same", NOW)
        b = core.initialize("Synthetic B", "UTC", "same", NOW)
        self.assertNotEqual(a["workspace_id"], b["workspace_id"])

    def test_public_repository_cannot_hold_state(self):
        with self.assertRaises(core.PilotError):
            core.Store(ROOT / "participant-private")

    def test_lock_prevents_concurrent_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            with core.Store(directory):
                with self.assertRaises(core.PilotError):
                    with core.Store(directory):
                        pass

    def test_atomic_save_reload_and_no_residual_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with core.Store(directory) as store:
                state = participant()
                store.save(state)
                self.assertEqual(state, store.load())
                self.assertEqual({"state.json", ".write-lock"}, {p.name for p in Path(directory).iterdir()})
            self.assertFalse((Path(directory)/".write-lock").exists())

    def test_nonfinite_json_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"bad.json"
            path.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaises(core.PilotError):
                core.read_json(path)


if __name__ == "__main__":
    unittest.main()
