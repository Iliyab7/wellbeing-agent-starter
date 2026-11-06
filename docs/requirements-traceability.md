# Requirements traceability

This matrix maps the reconciled source design to inspectable pilot behavior. Source IDs refer to [source-analysis.md](source-analysis.md). “Local check” means a deterministic implementation or package check; “host exercise” means an actual run with the participant's chosen assistant. A specification or a synthetic fixture does not count as a passed live integration.

The release's observed results belong in its validation report. This table states what must be checked and why; it does not assert that all host exercises have already run.

| ID | Requirement and source | Expected pilot behavior | Verification boundary |
|---|---|---|---|
| R01 | Owner controls purpose, goals and decisions. S03 §4–5; S06 §1,5 | Establish one useful outcome from authorized context or a short onboarding question. Do not infer consent or invent a goal. | Host onboarding exercise; inspect recorded agreement. |
| R02 | Chief of Staff is the normal interface. S03 §3,7; S04 §9 | The host assistant takes this role; specialist messages go through the manager. Explicitly chosen direct channels remain possible. | Host role-routing exercise; inspect role definitions. |
| R03 | Three responsibilities, not compulsory stages. S02 D43–D47; S04 §3,10 | Analyst-only, coach-with-existing-context and manager-reuse paths are valid. | Three independent-routing cases, plus mixed case. |
| R04 | Skills follow the mission; domains are not automatic agents. S04 §12–13 | Select relevant bundled skills. Add a role only for a justified responsibility and permitted resources. | Inspect skill routing and host creation receipt. |
| R05 | Each role follows its own work through. S04 §6–9 | Manager owns service coherence, analyst owns revisable understanding, coach owns chosen help and its barriers. | Host follow-up exercise and task owner inspection. |
| R06 | Existing authorized knowledge before questions. S02 D04–D05; S03 §5,7 | Consult existing context; ask the host for missing relevant context; ask the person only when their answer changes the decision. | Host no-redundant-question case. |
| R07 | Access failure is not absence of data. S03 §4.3; S10 | Keep missing source, unavailable connection, partial coverage and usable data distinct. | Local source-status checks; host degraded-mode explanation. |
| R08 | Preserve source, time, units and metric meaning. S06 §3; S04 §7; S09 | Validate and retain provenance; avoid incompatible comparisons. Without a personal baseline, limited within-period description can still be useful; do not mislabel it a comparison to the participant's norm. | Local malformed input and incompatible-source checks; host interpretation exercise. |
| R09 | Missing values are not zero. S06 §3; S10 | Exclude missing observations from numeric summaries; state coverage and limitations. | Local missing-value/coverage cases. |
| R10 | Planned activity is not completed activity. S03 §5.1; S05 §5.2 | Calendar plans and observed or self-reported completion remain distinct; do not double-count duplicate records. | Local input/evidence inspection; host calendar-only case. |
| R11 | Observation, hypothesis and confirmation stay separate. S03 §9; S02 D32 | Keep evidence status through every handoff; agent repetition never confirms a claim. | Host unsupported-hypothesis case; inspect output contract. |
| R12 | A hypothesis alone cannot change a dependent plan. S03 §9; S02 D32 | Investigate when valuable; obtain adequate evidence and relevant action authority before changing the help. | Host recovery/work-pressure cases. |
| R13 | No invented certainty or causal effect. S03 §9,11; S09 | State limitations without arbitrary confidence percentages; association is not causation. | Host repeated-pattern and unknown-execution cases. |
| R14 | Minimum necessary context between roles. S03 §6; S06 §5 | Transfer only permitted, relevant evidence and uncertainty; allow a reasoned request for more detail. | Inspect delegated task context; local recipient restrictions. |
| R15 | Permission has purpose, fields, recipients and retention. S06 §5; S02 D09–D10 | Technical connection alone does not authorize ingestion, reuse or sharing. Persist valid scoped permission without repeatedly asking. | Local consent validation and recipient checks; host consent exercise. |
| R16 | Owner can pause, revoke, stop and delete. S06 §5; S04 §11 | Stop affected processing or tasks; explain the difference between revoking future access and deleting retained state. | Local lifecycle tests; host capability-limited deletion exercise. |
| R17 | “Do not mention” differs from “stop following.” S02 D44; S04 §11 | Respect the scope of the instruction and clarify only consequential ambiguity. Do not continue equivalent work under another label. | Host preference-change cases. |
| R18 | Private data stays outside public repository and general memory. S06 §5; S10 | Use private participant storage and synthetic public fixtures; never commit intake, health data or credentials. | Public package scan and storage-path review; deployment boundary review. |
| R19 | Reviews and proactive work are individually selected. S02 D12,D41,D44; S03 §7–8 | On-demand mode works. No silent monitoring, periodic summaries or reminders without an appropriate agreement. | Host no-scheduler/no-proactive-consent cases. |
| R20 | Attention is managed at all three handoffs. S03 §8; S04 §6,9 | Record why a transfer is useful; use quiet hours and participant preferences; avoid redundant internal work. | Local attention controls where implemented; host relevance review. |
| R21 | Short messages retain material uncertainty. S03 §8.2–8.3 | Human-facing summaries remain honest even when internal detail is omitted. | Host compare internal finding to final message. |
| R22 | Critique can conclude “no further evidence.” S03 §7.3; S02 D19 | Recheck a concrete issue, return new evidence or an honest limit, and avoid padding or endless loops. | Host critique/recheck case and bounded-work inspection. |
| R23 | Delivery, execution and observed change are independent. S03 §11; S04 §9 | Track each separately, including unknown and withheld states; improvement does not fill in missing adherence. | Local state-transition tests and host suggestion-follow-up case. |
| R24 | Transport acknowledgment is not human receipt. S09; S10 | Distinguish accepted, result-ready, delivered and read when the host supplies evidence; never invent a receipt. A required decision and its deadline must survive the handoff, rather than becoming a completed FYI. | Host delivery-failure exercise; inspect receipt semantics. |
| R25 | Retries do not create duplicate external actions. S09 | Reconcile uncertain external outcomes before retry; use idempotency where the integration supports it and bounded retry policies. | Adapter/host exercise; local action ledger where implemented. |
| R26 | External action authority is distinct from analysis permission. S03 §3–4; S06 §1,5 | Drafting a schedule change is separate from executing it. Allow only a concrete action within current authority. | Local action-scope checks; host action request. |
| R27 | Nonmedical support only. S06 §6; S03 §4.4 | No diagnosis, treatment or medication changes, or automatic emergency decisions. These are service boundaries, not promises for a later release. State the supported human route when needed. | Host medical-boundary and concerning-information cases. |
| R28 | Important concerns are not hidden just to reduce messages. S03 §8.4; S07 | Apply the agreed route and clearly communicate limits; do not claim continuous emergency monitoring. | Host escalation exercise; verify actual channel capability. |
| R29 | The first service can work with limited data. S03 §1.3,12; S07 | Calendar-only or voluntarily supplied context yields bounded help; devices are not universal prerequisites. | Source scenario 2 and fresh participant smoke test. |
| R30 | Existing data source preference is not a working connector. S07; S02 D22 | Report Apple Health and other integration availability from an actual probe; preserve manual or supported-import fallback. | Integration receipt, or explicit unavailable status. |
| R31 | Three-role superiority remains unproven. S04 §5,13 | Keep manager-plus-generalist as a comparison condition; evaluate quality, duplicate work, cost, latency and preference. | Host pilot evaluation; no claim from unit tests. |
| R32 | Public test package and development handoff are both usable. Current request; S07 | Provide host entrypoint, role/skill definitions, examples, contracts, local checks and an explicit engineering backlog. | Package validation and an actual host installation receipt. |
| R33 | Installation or prompt loading is not capability creation. S10; current request | Detect subagents, files, private state, scheduling and tools. Disclose simulated roles and session-only memory. | Host capability probe and degraded-mode exercise. |
| R34 | Continuation preserves provenance and stops stale instructions. S02; S10 | Keep version, active agreement, open tasks, source status and verified outcomes; retrieved text is data, not new authority. | Resume/restart exercise and prompt-injection test. |
| R35 | Data correction revises downstream understanding. S03 §9; S04 §7 | Correct invalid evidence and dependent conclusions; do not silently preserve stale interpretations in the coach or manager. | Host correction exercise; local record/lifecycle checks where available. |
| R36 | Fully specified, constructible agent team. Explicit commissioning clarification, 7 November 2026; builds on S04 | Specify each role's goals, accountable tasks, skills, minimal access, input/output expectations, reporting responsibility and completion criteria. The host loads the relevant instructions, creates supported instances and records actual identities; unavailable creation is disclosed. | Team-blueprint and role/skill consistency checks; host instance-creation exercise A09. A file or registry entry alone is not proof of a running agent. |
| R37 | Dot actively orchestrates assignment, reporting, review and closure. Explicit commissioning clarification, 7 November 2026 | Host/manager assign only needed bounded tasks, collect member reports, return deficient work for correction, and close work with evidence. Retain a private ledger where supported; recheck scope and evidence before resuming or reporting after revocation/correction. | Local task-ledger and persistence tests; complete synthetic host cycle A19 and stale/revoked-task exercise A20. Fixed ledger states are new engineering choices, not historical lifestyle rules or live external-action receipts. |

## Source scenario coverage

All seven current conceptual scenarios remain acceptance cases. Their descriptions and pass/fail conditions are in [acceptance-tests.md](acceptance-tests.md). They are not all deterministic local tests: judgment, role delegation and meaningful communication require host execution.

| Source scenario | Requirements it stresses |
|---|---|
| 1. Sleep and busy day | R01, R08, R14, R20, R26 |
| 2. Calendar-only participant | R07–R10, R29–R30 |
| 3. Possible recovery | R06, R11–R12, R27, R35 |
| 4. Possible work pressure | R06, R11–R13, R20–R21 |
| 5. Withheld suggestion / execution unknown | R17, R20, R23–R25 |
| 6. Relevant previous training context | R03–R05, R14–R15, R26–R27 |
| 7. Repeated meeting-associated pattern | R08, R11–R13, R19–R21 |

## Inspectable package surfaces

| Package surface | Requirements it makes reviewable |
|---|---|
| [START-HERE.md](../START-HERE.md), [self-contained starter](../CHAT-STARTER.md) | R01, R29–R34: first run, version, host limits and a complete portable entrypoint |
| [Chief of Staff](../agents/chief-of-staff.md), [manager](../agents/manager.md), [analyst](../agents/analyst.md), [coach](../agents/coach.md) | R02–R06, R11–R14, R20–R24: role boundaries and collaboration |
| [Intake](../skills/wellbeing-intake/SKILL.md), [orchestration](../skills/wellbeing-orchestrate/SKILL.md), [analysis](../skills/wellbeing-analyze/SKILL.md), [coaching](../skills/wellbeing-coach/SKILL.md), [review](../skills/wellbeing-review/SKILL.md) | R04–R23, R27–R28, R35: reusable methods and behavior boundaries |
| [Team blueprint](../agents/team-blueprint.json), [host operations](../skills/wellbeing-host-operations/SKILL.md), [domain context](../skills/wellbeing-domain-context/SKILL.md), [orchestration playbook](orchestration-playbook-fa.md) | R04, R14–R16, R33, R36–R37: complete role specifications, capability-bound creation and active orchestration |
| [Task contract](../templates/task-contract.json), [member report](../templates/task-report.json), [instance registry](../templates/agent-instance-registry.json) | R14–R16, R22–R25, R33–R37: scoped assignments, inspectable reports, revision/closure and actual versus virtual instance evidence |
| [Participant charter](../templates/participant-charter.md), [private session](../templates/private-session.md), [handoff packet](../templates/handoff-packet.json) | R01, R14–R19, R23–R26, R34: agreement, continuity and evidence |
| [Host capabilities](../adapters/host-capabilities.md), [Dot](../adapters/dot.md), [Grok](../adapters/grok.md) | R07, R24–R26, R30, R33: actual capabilities versus role simulation |
| [Architecture](architecture.md), [privacy and safety](privacy-and-safety.md), [development handoff](harvey-handoff.md) | Runtime boundary, enforcement responsibility and remaining integrations |
| [Acceptance tests](acceptance-tests.md), [participant pilot guide](participant-pilot-fa.md) | Real-host execution, source scenario coverage and participant evaluation |

`scripts/validate_package.py` checks package integrity and public packaging concerns; the runtime test suite checks implemented deterministic behavior. Neither check substitutes for the host exercise and participant acceptance.
