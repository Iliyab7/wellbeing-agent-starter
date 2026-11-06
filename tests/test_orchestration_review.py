"""Independent task-ledger checks. All task reports and receipts are synthetic."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wellbeing import core, tasks
from test_independent_review import NOW, configured, policy, record


def contract(task_id="review-task", evidence=True):
    return {"id": task_id, "role": "analyst", "goal": "Answer the synthetic data question",
            "purpose": policy()["purpose"], "evidence_ids": ["one"] if evidence else [],
            "acceptance": ["Distinguish observed values from missing observations"],
            "requested_output": "A concise synthetic report with uncertainty", "deadline": None}


def report_payload(state, task_id="review-task"):
    return {"task_id": task_id, "role": "analyst", "policy_revision": state["policy_revision"],
            "observations": ["A synthetic observation is available"],
            "uncertainty": ["No cause was established"], "requested_decisions": [],
            "evidence_ids": ["one"], "result": "Synthetic report; no medical conclusion",
            "receipt_ref": "synthetic-agent-receipt-1"}


def prepared(evidence=True):
    state = configured()
    if evidence:
        core.import_records(state, [record()], now=NOW)
    tasks.create(state, contract(evidence=evidence), now=NOW)
    return state


class OrchestrationReviewTests(unittest.TestCase):
    def test_task_idempotency_does_not_overwrite_different_work(self):
        state = prepared()
        self.assertEqual(tasks.create(state, contract(), now=NOW)["status"], "prepared")
        self.assertEqual(len(state["tasks"]), 1)
        changed = contract()
        changed["requested_output"] = "Different request"
        with self.assertRaises(core.PilotError):
            tasks.create(state, changed, now=NOW)
        self.assertEqual(state["tasks"]["review-task"]["contract"], contract())

    def test_task_requires_both_role_and_evidence_permission(self):
        state = configured()
        core.import_records(state, [record()], now=NOW)
        denied = contract()
        denied["role"] = "coach"
        with self.assertRaises(core.PilotError):
            tasks.create(state, denied, now=NOW)
        self.assertFalse(state.get("tasks"))

    def test_unknown_dispatch_requires_reconciliation_before_retry(self):
        state = prepared()
        tasks.dispatch(state, "review-task", "synthetic-attempt", unknown=True, now=NOW)
        with self.assertRaises(core.PilotError):
            tasks.dispatch(state, "review-task", "synthetic-retry", now=NOW)
        with self.assertRaises(core.PilotError):
            tasks.report(state, "review-task", report_payload(state), now=NOW)
        tasks.reconcile(state, "review-task", "not_sent", "synthetic-tool-readback", now=NOW)
        self.assertEqual(tasks.dispatch(state, "review-task", "synthetic-new-attempt", now=NOW)["status"], "dispatched")

    def test_report_receipt_acceptance_and_closure_are_distinct(self):
        state = prepared()
        with self.assertRaises(core.PilotError):
            tasks.report(state, "review-task", report_payload(state), now=NOW)
        tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW)
        received = tasks.report(state, "review-task", report_payload(state), now=NOW)
        self.assertEqual(received["status"], "report_received")
        with self.assertRaises(core.PilotError):
            tasks.close(state, "review-task", "Too early", now=NOW)
        accepted = tasks.review(state, "review-task", "accept", "Synthetic checks met", now=NOW)
        self.assertEqual(accepted["status"], "verified")
        self.assertEqual(accepted["reviews"][-1]["provenance"], "host_review")
        closed = tasks.close(state, "review-task", "Internal task complete", now=NOW)
        self.assertEqual(closed["status"], "closed")
        self.assertNotIn("human_delivered", closed)

    def test_wrong_report_role_revision_and_evidence_are_rejected(self):
        for field, value in (("role", "coach"), ("policy_revision", 999), ("evidence_ids", ["unassigned"])):
            with self.subTest(field=field):
                state = prepared()
                tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW)
                payload = report_payload(state)
                payload[field] = value
                with self.assertRaises(core.PilotError):
                    tasks.report(state, "review-task", payload, now=NOW)
                self.assertEqual(state["tasks"]["review-task"]["status"], "dispatched")
                self.assertIsNone(state["tasks"]["review-task"]["report"])

    def test_duplicate_report_is_idempotent_but_revise_requires_new_content(self):
        state = prepared()
        tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW)
        payload = report_payload(state)
        tasks.report(state, "review-task", payload, now=NOW)
        before = copy.deepcopy(state["tasks"]["review-task"])
        tasks.report(state, "review-task", payload, now=NOW)
        self.assertEqual(state["tasks"]["review-task"], before)
        tasks.review(state, "review-task", "revise", "Clarify the uncertainty", now=NOW)
        with self.assertRaises(core.PilotError):
            tasks.report(state, "review-task", payload, now=NOW)
        payload["uncertainty"] = ["Only one synthetic observation; no trend or cause established"]
        self.assertEqual(tasks.report(state, "review-task", payload, now=NOW)["status"], "report_received")

    def test_pause_blocks_work_but_allows_receipt_reconciliation_and_cancel(self):
        state = prepared()
        tasks.dispatch(state, "review-task", "synthetic-attempt", unknown=True, now=NOW)
        core.pause(state, now=NOW)
        self.assertEqual(tasks.show(state, "review-task", now=NOW)["status"], "dispatch_unknown")
        tasks.reconcile(state, "review-task", "sent", "synthetic-readback", now=NOW)
        with self.assertRaises(core.PilotError):
            tasks.report(state, "review-task", report_payload(state), now=NOW)
        self.assertEqual(tasks.cancel(state, "review-task", "Participant stopped work", now=NOW)["status"], "cancelled")
        self.assertEqual(state["status"], "paused")

    def test_correction_invalidates_outstanding_task_context(self):
        state = prepared()
        core.correct_record(state, record(value=7), confirmed=True, now=NOW)
        task = tasks.show(state, "review-task", now=NOW)
        self.assertEqual(task["status"], "invalidated")
        self.assertFalse(task["data_valid"])
        self.assertNotIn("contract", task)
        with self.assertRaises(core.PilotError):
            tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW)

    def test_revocation_clears_closed_report_but_keeps_completion_receipt(self):
        state = prepared()
        tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW)
        tasks.report(state, "review-task", report_payload(state), now=NOW)
        tasks.review(state, "review-task", "accept", "Synthetic checks met", now=NOW)
        tasks.close(state, "review-task", "Internal task complete", now=NOW)
        core.revoke(state, "manual", now=NOW)
        task = tasks.show(state, "review-task", now=NOW)
        self.assertEqual(task["status"], "closed")
        self.assertFalse(task["data_valid"])
        self.assertNotIn("report", task)
        self.assertNotIn("contract", task)
        self.assertTrue(any(e["event"] == "closed" for e in task["events"]))

    def test_deadline_and_consent_expiry_block_dispatch(self):
        for kind in ("deadline", "consent"):
            with self.subTest(kind=kind):
                p = policy()
                if kind == "consent":
                    p["valid_until"] = (NOW + timedelta(hours=1)).isoformat()
                state = configured(p)
                task = contract(evidence=False)
                if kind == "deadline":
                    task["deadline"] = (NOW + timedelta(hours=1)).isoformat()
                tasks.create(state, task, now=NOW)
                with self.assertRaises(core.PilotError):
                    tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW + timedelta(hours=2))
                self.assertFalse(state["tasks"]["review-task"]["data_valid"])

    def test_empty_evidence_task_cannot_outlive_retention(self):
        state = prepared(evidence=False)
        with self.assertRaises(core.PilotError):
            tasks.dispatch(state, "review-task", "synthetic-dispatch", now=NOW + timedelta(days=20))
        self.assertFalse(state["tasks"]["review-task"]["data_valid"])

    def test_context_contains_only_task_evidence_and_is_detached(self):
        state = prepared()
        core.import_records(state, [record("unrelated", 99, 2)], now=NOW)
        core.checkin(state, "SYNTHETIC-PRIVATE-JOURNAL-NOT-FOR-TASK", now=NOW)
        context = tasks.context(state, "review-task", now=NOW)
        self.assertEqual([r["id"] for r in context["evidence"]], ["one"])
        self.assertNotIn("unrelated", json.dumps(context))
        self.assertNotIn("SYNTHETIC-PRIVATE-JOURNAL-NOT-FOR-TASK", json.dumps(context))
        self.assertEqual(context["receipt"], "prepared_not_sent")
        self.assertEqual(context["tools"], [])
        context["acceptance"].append("Caller-local edit")
        context["evidence"][0]["value"] = 123
        self.assertEqual(state["tasks"]["review-task"]["contract"]["acceptance"], contract()["acceptance"])
        self.assertEqual(state["records"][0]["value"], 8)

    def test_task_cli_roundtrip_keeps_internal_acceptance_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "private"

            def run(*args, expected=0):
                proc = subprocess.run([sys.executable, "-m", "wellbeing", "--home", str(home), *args],
                                      cwd=core.ROOT, capture_output=True, text=True)
                self.assertEqual(proc.returncode, expected, proc.stderr)
                return json.loads(proc.stdout if expected == 0 else proc.stderr)

            run("init", "--goal", "Synthetic CLI review", "--timezone", "UTC")
            p = base / "policy.json"
            p.write_text(json.dumps(policy()), encoding="utf-8")
            run("configure", "--file", str(p), "--confirmed")
            c = base / "task.json"
            c.write_text(json.dumps(contract(evidence=False)), encoding="utf-8")
            run("task", "create", "--file", str(c))
            run("task", "dispatch-unknown", "--id", "review-task", "--receipt-ref", "synthetic-attempt")
            run("task", "dispatch", "--id", "review-task", "--receipt-ref", "synthetic-retry", expected=2)
            run("task", "reconcile", "--id", "review-task", "--outcome", "sent", "--receipt-ref", "synthetic-readback")
            payload = report_payload({"policy_revision": 1})
            payload["evidence_ids"] = []
            r = base / "report.json"
            r.write_text(json.dumps(payload), encoding="utf-8")
            received = run("task", "report", "--id", "review-task", "--file", str(r))
            self.assertEqual(received["result"]["status"], "report_received")
            run("task", "close", "--id", "review-task", "--reason", "Too early", expected=2)
            run("task", "review", "--id", "review-task", "--decision", "accept", "--reason", "Synthetic criteria met")
            run("task", "close", "--id", "review-task", "--reason", "Internal task complete")
            self.assertEqual(run("task", "show", "--id", "review-task")["result"]["status"], "closed")


if __name__ == "__main__":
    unittest.main()
