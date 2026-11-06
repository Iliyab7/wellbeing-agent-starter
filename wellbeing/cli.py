"""CLI transport. JSON output is for the host; no external service is contacted."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import core
from . import tasks


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--home", help="Private workspace outside this checkout; default ~/.wellbeing-starter")
    sub = result.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize one participant; no data consent is inferred")
    group = init.add_mutually_exclusive_group(required=True)
    group.add_argument("--goal")
    group.add_argument("--goal-file", help="UTF-8 goal file avoids personal text in shell history")
    init.add_argument("--timezone", required=True)
    init.add_argument("--alias", default="participant")
    config = sub.add_parser("configure")
    config.add_argument("--file", required=True)
    config.add_argument("--confirmed", action="store_true")
    config.add_argument("--consent-reference", help="Private pointer to the participant's agreement; never a fabricated receipt")
    imp = sub.add_parser("import", help="Import a consented JSON list transactionally")
    imp.add_argument("--file", required=True)
    correct = sub.add_parser("correct")
    correct.add_argument("--file", required=True, help="One corrected record object with the original ID")
    correct.add_argument("--confirmed", action="store_true")
    remove_record = sub.add_parser("delete-record")
    remove_record.add_argument("--id", required=True)
    remove_record.add_argument("--confirmed", action="store_true")
    source = sub.add_parser("source-status")
    source.add_argument("--source", required=True)
    source.add_argument("--status", choices=["available", "absent", "partial", "stale", "conflicting", "technical_failure", "not_checked"], required=True)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--source", required=True)
    analysis.add_argument("--metric", required=True)
    analysis.add_argument("--since")
    analysis.add_argument("--until")
    checkin = sub.add_parser("check-in")
    add_text_arguments(checkin)
    plan = sub.add_parser("plan")
    add_text_arguments(plan)
    plan.add_argument("--evidence", action="append", default=[])
    review = sub.add_parser("review")
    review.add_argument("--plan-id", required=True)
    review.add_argument("--decision", choices=["proposed", "accepted", "declined", "paused"])
    review.add_argument("--receipt", choices=["unknown", "not_delivered", "withheld", "failed", "delivered", "acknowledged"])
    review.add_argument("--implementation", choices=["unknown", "not_started", "tried", "ongoing", "completed", "blocked"])
    outcome = review.add_mutually_exclusive_group()
    outcome.add_argument("--outcome")
    outcome.add_argument("--outcome-file")
    goal = sub.add_parser("set-goal")
    add_text_arguments(goal)
    goal.add_argument("--confirmed", action="store_true")
    goal.add_argument("--same-purpose", action="store_true", help="Host attests change stays within the participant's existing purpose and permissions")
    team = sub.add_parser("team")
    team.add_argument("--mode", choices=["inline", "native"], default="inline")
    packet = sub.add_parser("packet")
    packet.add_argument("--role", required=True, choices=core.ROLES)
    packet.add_argument("--task", required=True)
    packet.add_argument("--source")
    packet.add_argument("--metric")
    packet.add_argument("--output", help="Optional new private JSON file outside the checkout")
    verify = sub.add_parser("verify-packet")
    verify.add_argument("--file", required=True)
    sub.add_parser("status")
    sub.add_parser("pause")
    resume = sub.add_parser("resume")
    resume.add_argument("--confirmed", action="store_true")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("--source", required=True)
    export = sub.add_parser("export")
    export.add_argument("--file", required=True)
    export.add_argument("--confirmed", action="store_true")
    delete = sub.add_parser("delete")
    delete.add_argument("--confirmed", action="store_true")
    task = sub.add_parser("task", help="Private internal assignment/report ledger; no agent execution")
    task_commands = task.add_subparsers(dest="task_command", required=True)
    task_create = task_commands.add_parser("create")
    task_create.add_argument("--file", required=True)
    for operation in ("dispatch", "dispatch-unknown", "reconcile"):
        operation_parser = task_commands.add_parser(operation)
        operation_parser.add_argument("--id", required=True)
        operation_parser.add_argument("--receipt-ref", required=True)
        if operation == "reconcile":
            operation_parser.add_argument("--outcome", choices=["sent", "not_sent"], required=True)
    task_report = task_commands.add_parser("report")
    task_report.add_argument("--id", required=True)
    task_report.add_argument("--file", required=True)
    for operation in ("review", "close", "cancel"):
        operation_parser = task_commands.add_parser(operation)
        operation_parser.add_argument("--id", required=True)
        reason = operation_parser.add_mutually_exclusive_group(required=True)
        reason.add_argument("--reason")
        reason.add_argument("--reason-file")
        if operation == "review":
            operation_parser.add_argument("--decision", choices=["accept", "revise"], required=True)
    task_show = task_commands.add_parser("show")
    task_show.add_argument("--id", required=True)
    task_context = task_commands.add_parser("context")
    task_context.add_argument("--id", required=True)
    task_context.add_argument("--output", help="New private JSON file outside the checkout")
    return result


def add_text_arguments(command):
    group = command.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--text-file", help="UTF-8 private file avoids personal text in shell history")


def input_text(args, field="text"):
    file = getattr(args, field + "_file", None)
    if file:
        try:
            return Path(file).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise core.PilotError("Cannot read the chosen UTF-8 private text file.") from exc
    return getattr(args, field, None)


def execute(args):
    with core.Store(args.home) as store:
        if args.command == "init":
            core.require(not store.path.exists(), "Workspace already exists. Use a separate private directory for each participant.")
            state = core.initialize(input_text(args, "goal"), args.timezone, args.alias)
            store.save(state)
            return {"status": state["status"], "home": str(store.home), "next": "Agree a policy, then configure --file POLICY --confirmed."}
        state = store.load()
        core.prune(state)
        tasks.refresh(state)
        if args.command == "configure":
            result = core.configure(state, core.read_json(args.file), args.confirmed, consent_reference=args.consent_reference)
        elif args.command == "import":
            result = core.import_records(state, core.read_json(args.file))
        elif args.command == "correct":
            result = core.correct_record(state, core.read_json(args.file), args.confirmed)
        elif args.command == "delete-record":
            result = core.delete_record(state, args.id, args.confirmed)
        elif args.command == "source-status":
            core.set_source_status(state, args.source, args.status)
            result = {"source": args.source, "status": args.status}
        elif args.command == "analyze":
            result = core.analyze(state, args.source, args.metric, args.since, args.until)
        elif args.command == "check-in":
            result = core.checkin(state, input_text(args))
        elif args.command == "plan":
            result = core.create_plan(state, input_text(args), args.evidence)
        elif args.command == "review":
            result = core.review_plan(state, args.plan_id, args.decision, args.receipt, args.implementation, input_text(args, "outcome"))
        elif args.command == "set-goal":
            result = core.set_goal(state, input_text(args), args.confirmed, args.same_purpose)
        elif args.command == "team":
            result = core.team(state, args.mode)
        elif args.command == "packet":
            result = core.packet(state, args.role, args.task, args.source, args.metric)
            if args.output:
                path = core.private_path(args.output)
                core.require(not path.exists(), "Packet output already exists; choose a new path.")
                core.atomic_json(path, result)
        elif args.command == "verify-packet":
            result = core.verify_packet(state, core.read_json(args.file))
        elif args.command == "status":
            result = core.status(state)
        elif args.command == "pause":
            core.pause(state)
            result = {"status": state["status"]}
        elif args.command == "resume":
            core.resume(state, args.confirmed)
            result = {"status": state["status"]}
        elif args.command == "revoke":
            result = core.revoke(state, args.source)
        elif args.command == "export":
            result = core.export_state(state, args.file, args.confirmed)
        elif args.command == "delete":
            core.require(args.confirmed, "Deletion requires an explicit participant request and --confirmed.")
            store.path.unlink()
            return {"status": "deleted", "scope": "This workspace state.json only.",
                    "remaining": "Host memory, exported packets, backups and external copies require separate deletion. Secure physical erasure is not guaranteed."}
        elif args.command == "task":
            if args.task_command == "create":
                result = tasks.create(state, core.read_json(args.file))
            elif args.task_command in ("dispatch", "dispatch-unknown"):
                result = tasks.dispatch(state, args.id, args.receipt_ref, unknown=args.task_command == "dispatch-unknown")
            elif args.task_command == "reconcile":
                result = tasks.reconcile(state, args.id, args.outcome, args.receipt_ref)
            elif args.task_command == "report":
                result = tasks.report(state, args.id, core.read_json(args.file))
            elif args.task_command == "review":
                result = tasks.review(state, args.id, args.decision, input_text(args, "reason"))
            elif args.task_command == "close":
                result = tasks.close(state, args.id, input_text(args, "reason"))
            elif args.task_command == "cancel":
                result = tasks.cancel(state, args.id, input_text(args, "reason"))
            elif args.task_command == "context":
                result = tasks.context(state, args.id)
                if args.output:
                    destination = core.private_path(args.output)
                    core.require(not destination.exists(), "Task context output already exists; choose a new path.")
                    core.atomic_json(destination, result)
            else:
                result = tasks.show(state, args.id)
        else:
            raise core.PilotError("Unknown command.")
        tasks.refresh(state)
        store.save(state)
        return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = execute(args)
    except (core.PilotError, OSError) as exc:
        # Validation messages do not echo imported participant payloads.
        # ASCII-escaped JSON is a valid UTF-8 subset and is safe on legacy redirected
        # consoles. Output must not fail *after* a successful state commit.
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    except (KeyError, TypeError, OverflowError) as exc:
        print(json.dumps({"ok": False, "error": "Malformed state or input structure; no requested operation was committed."}), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=True, indent=2, allow_nan=False))
    return 0
