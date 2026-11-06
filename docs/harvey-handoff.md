# Harvey / development-team handoff

## What is being delivered

A portable initial-test package for a personal Wellbeing team. The participant's existing assistant acts as Chief of Staff; Dot is the requested first host, while another assistant can use the same protocol if it has sufficient capabilities. The proposed internal team consists of Manager, Analyst and Coach. This is a pilot implementation of the documented design, with an inspectable Python reference harness and a conversation-only path.

The desired first user journey is: give the assistant the repository or starter file → discover actual capabilities → reuse authorized context → choose one goal and close missing data/authority decisions → initialize the appropriate role mode → deliver useful, bounded help → review, correct, resume or stop. A participant should not need to understand agent plumbing or maintain three separate conversations.

## Reading and running order

1. Read [START-HERE](../START-HERE.md), [architecture](architecture.md) and [source analysis](source-analysis.md).
2. Read [requirements traceability](requirements-traceability.md) to distinguish inherited design, new pilot choices and unresolved production decisions.
3. Follow [runtime.md](runtime.md) for the actual local CLI and synthetic demo.
4. Run `python -m unittest discover -s tests -v` and `python scripts/validate_package.py` from the repository root.
5. Use [CHAT-STARTER.md](../CHAT-STARTER.md) in the chosen host with synthetic inputs. Exercise the [acceptance cases](acceptance-tests.md); retain actual capability receipts.
6. Begin a personal trial only within the participant's chosen charter and storage environment. Use [the participant guide](participant-pilot-fa.md).

The Python path needs Python 3.11 or later and uses the standard library. The conversation-only path requires neither a Python installation nor an API key from the participant. Access to a capable assistant remains necessary. Do not request account passwords or put provider keys into this repository.

## Deliverable map

| Area | Entry point | Purpose |
|---|---|---|
| Participant entry | [START-HERE.md](../START-HERE.md) | Choose the available trial route |
| One-file host protocol | [CHAT-STARTER.md](../CHAT-STARTER.md) | Start when the host cannot browse/clone a repository |
| Roles | [registry.json](../agents/registry.json) | Role instructions and responsibilities |
| Operational definitions | [team blueprint](../agents/team-blueprint.json), [orchestration playbook](orchestration-playbook-fa.md) | Per-agent goals, tasks, access, skills and management lifecycle |
| Skills | [host operations](../skills/wellbeing-host-operations/SKILL.md), [intake](../skills/wellbeing-intake/SKILL.md), [orchestration](../skills/wellbeing-orchestrate/SKILL.md), [analysis](../skills/wellbeing-analyze/SKILL.md), [coaching](../skills/wellbeing-coach/SKILL.md), [domain context](../skills/wellbeing-domain-context/SKILL.md), [review](../skills/wellbeing-review/SKILL.md) | Reusable behavior under scoped authority |
| Task/report lifecycle | [task contract](../templates/task-contract.json), [task report](../templates/task-report.json), [instance registry](../templates/agent-instance-registry.json) | Trace assignment, actual dispatch, returned work, verification and closure |
| Host contracts | [capabilities](../adapters/host-capabilities.md), [Dot](../adapters/dot.md), [Grok](../adapters/grok.md) | Capability discovery and honest fallback |
| Runtime | [runtime.md](runtime.md) | Implemented commands, state and constraints |
| Trial records | [participant charter](../templates/participant-charter.md), [feedback](../templates/test-feedback.md) | Private participant agreement and evaluation |
| Validation | [acceptance tests](acceptance-tests.md), [validator](../scripts/validate_package.py) | Reproducible checks and host evaluation |
| Release | [package-manifest.json](../package-manifest.json) | Exact package files and hashes |

The conversational templates and Python input schemas are distinct. Do not feed a host template to the CLI unless its command explicitly accepts that format.

## Implemented contract versus host responsibility

The runtime demonstrates local evidence handling, explicit settings, state transitions and scoped handoffs. The host handles natural-language judgment, role selection, user interaction and any real subagent creation. A role instruction file does not itself create an agent. A generated handoff packet does not itself transfer data. A reminder preference does not itself schedule a job.

For real host actions, distinguish capability availability, an attempted operation, verified success, failure and an unknown result according to observed evidence; use the exact fields defined by the selected adapter or runtime. Only use an actual vendor capability exposed to that host; do not build against a guessed Dot/Grok endpoint. The package does not hardcode model IDs, proprietary SDK versions or external API credentials.

## Operational handoff acceptance

Demonstrate the whole management loop, not just loading the starter: the host reads the blueprint, loads role skills, creates or selects the appropriate real/virtual instance, assigns a bounded task, records actual dispatch evidence when applicable, receives a structured report, verifies it, requests revision if needed, and closes or schedules an authorized next step. The participant receives useful conclusions through the Chief of Staff instead of managing the internal queue.

Trace the same task ID across assignment, report and review. Record actual agent instance IDs only if creation occurred. Keep role authority and participant consent separate from a role's self-reported competence. A prepared local task, a returned report, a verified result, a user-facing delivery and an executed real-world action are separate milestones. Review [A19 and A20](acceptance-tests.md) with synthetic input before personal use.

## Work to complete for a hosted product

| Workstream | Production acceptance condition |
|---|---|
| Host/agent runtime | Verified provisioning, scoped context transfer, cancellation, bounded retries, resource limits and real lifecycle receipts |
| Private persistence | Participant isolation, appropriate encryption/access control, retention enforcement, corrections, export/deletion and tested restore behavior |
| Wearable connectors | Real authentication, explicit metric mapping, source/unit/time-zone provenance, deduplication, freshness, permission revocation and failure states |
| Calendar/actions | Separate read/write authority; consequential operation review as needed; idempotency; no silent duplicate changes |
| Scheduling | Durable execution, time zones, quiet hours, deduplication, cancellation and honest failed-delivery handling |
| Observability | Useful operational evidence without personal records in logs; trace task/consent versions and side-effect receipts |
| Safety and privacy | Adversarial source-content tests, recipient isolation, source revocation, nonclinical boundary review and clear human escalation limits |
| Evaluation | Repeated synthetic tests plus participant feedback; compare team complexity against a simpler setup |

These are explicit remaining engineering tasks, not hidden prerequisites for a manual conversation-only pilot. A production deployment must name an operational owner and verify its own configuration; this public repository does not create infrastructure automatically.

## Decisions already made for this pilot

- Use the existing three-role proposal, while treating its practical benefit as an experiment.
- Let the host replace ELHAM as the normal participant-facing Chief of Staff.
- Start with one chosen goal and whatever useful authorized data exists. A wearable is optional.
- Support virtual roles when real subagent creation is unavailable; label the mode honestly.
- Keep private participant state outside the public source checkout. Use synthetic repository fixtures.
- Make reporting cadence, notifications, sources and action authority participant-specific.
- Preserve observation/hypothesis/confirmation and delivery/execution/outcome distinctions.

## Decisions to close per participant

The current goal, useful sources and metrics, permitted recipients, storage/retention, available tools, action authority, contact preferences and the next review point. Resolve existing authorized facts first; ask only the material gaps. Do not turn every open design question into a long first-session form.

## Maintenance and release

Keep source changes small enough to review. Run tests after meaningful code changes; run package validation after regenerating the manifest. A manifest mismatch is a release defect, not something to bypass by disabling checks. Release archives must contain only the public package; exclude private states, exports, original meeting transcripts, provider tokens and local review material.

Record observed verification against the exact release. CI verifies only the checks it runs. A local test pass, a GitHub push, an agent-generated transcript and a live participant trial are different evidence. Use synthetic minimal reproductions in public issues. Keep private feedback in the participant's chosen private channel; do not publish it by default.
