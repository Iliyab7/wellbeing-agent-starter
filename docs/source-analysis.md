# Source analysis and pilot decisions

This pilot turns the existing Wellbeing design into a portable package that a personal assistant can load and a development team can inspect. The participant's assistant acts as the **Chief of Staff**. Dot is one possible host for that role; the package does not depend on a product merely having that name.

## Provenance and interpretation

The design baseline is `Iliyab7/wellbeing-agent-definition` at commit `e43881ec638d7d01afbe4a609954577f187b1558`, whose current documentation was reconciled on 5 November 2026. The new request on 7 November 2026 authorizes a separate public pilot and makes the host assistant the executor and team coordinator. It does not turn historical examples into consent to process a participant's private data.

The source repository is private. The public package contains a fresh implementation and reusable synthesis; it does not redistribute conversations, personal records, account details, or the source archive. Maintainers with access can use the source references below. A new participant needs only this public package.

| Reference | Authoritative source at the pinned commit | Meaning |
|---|---|---|
| S01 | `START-HERE.md`, `context/CURRENT-STATE.md` | Latest baseline, acceptance limits and remaining design questions |
| S02 | `context/DOCUMENT-STATUS.md`, `context/DECISIONS.md` | Precedence and corrections, including D40–D47 and D58–D62 |
| S03 | `design/2026-11-02-wellbeing-team-design-fa.md` version 1.2 | Collaboration, attention, consent, uncertainty and seven scenarios |
| S04 | `design/2026-11-02-wellbeing-team-role-proposal-fa.md` | Responsibility-based manager, analyst and coach |
| S05 | `design/2026-11-02-wellbeing-missions-before-roles-fa.md` | Coverage of work; its seven activity families are not seven agents |
| S06 | `sources/author-brief-fa.md` | Ownership, data quality, scoped permissions and nonmedical boundary |
| S07 | `meetings/2026-10-31-kazemi/`, `design/2026-11-02-kazemi-session-alignment-fa.md` | Original delivery intent, simple roles, existing data and a familiar user channel |
| S08 | `reports/2026-11-02-wellbeing-simple/wellbeing-fa.md` | Accessible synthesis and role diagram |
| S09 | `history/`, `phase-01/`, `meeting-brief/`, `deliveries/2026-10-30-astra-definition/` | Historical learning, earlier proposals and useful counterexamples |
| S10 | `context/CONCEPTS.md`, `continuity/` | Meaning of agent, harness, skill, delivery and source continuity |

[Pinned design repository](https://github.com/Iliyab7/wellbeing-agent-definition/tree/e43881ec638d7d01afbe4a609954577f187b1558) requires source-repository access. S01–S10 are provenance labels, not bundled files.

The inventory contains 137 tracked files: 121 text files and 16 binary assets or packaged/rendered outputs. The substantive Markdown documents and both meeting transcripts are the textual basis of the review. Generated context packs, rendered HTML/SVG, build tools, manifests, QA receipts and binary assets are distinguished from independent product requirements. Existing PDF QA is historical evidence; this pilot does not claim a new visual inspection of those PDFs, a fresh unpacking of the old ZIP, or verification against the unavailable original meeting audio.

## What the design actually calls for

The participant should receive useful understanding and practical support without managing several agents. Useful support can mean answering one question, maintaining an already satisfactory routine, considering a small change, or arranging an authorized next step. Producing more reports is not the purpose.

| Role | Accountable result | Work it does not automatically own |
|---|---|---|
| Participant / owner | Goals, preferences and permission decisions | Day-to-day internal task routing |
| Chief of Staff, supplied by the host assistant | User relationship, authorized wider context, attention and external coordination | Inventing participant goals or granting itself new data scope |
| Wellbeing manager | Coherent service, clear task ownership, conflicts and follow-through | Repeating every specialist analysis or taking over the whole calendar |
| Situation and trends analyst | Evidence-based, revisable understanding | Producing a behavior-change plan for every observation |
| Goals and habits coach | Suitable, practical support and continuity of chosen help | Diagnosing conditions, changing treatment or inventing adherence |

The three Wellbeing roles are an initial implementation choice grounded in the accepted proposal. They are **not a compulsory sequence**. An analyst can finish a comparison question without invoking the coach. A coach can help adapt a chosen routine using valid existing context. A manager can reuse a current answer instead of commissioning new work.

Sleep, movement, nutrition, recovery and everyday wellbeing are domains in which skills may be needed. Their names do not justify a permanent agent each. A skill file describes a method; it is neither clinical qualification nor a working access-control mechanism.

## Corrections carried into the pilot

| Earlier interpretation | Current interpretation and pilot consequence |
|---|---|
| Start with a fixed sleep-review service. | Sleep was an earlier proposal. The participant chooses the first useful service; synthetic sleep data can test the package without choosing a real participant's goal. |
| Use seven agents or one agent per health domain. | Seven activities describe the work cycle. Roles follow independent responsibility; each role has its own complete work cycle. |
| Always pass from analyst to coach to a separate follower. | Route to the necessary role. The coach retains responsibility for its own help; the manager tracks the team's commitments. |
| Everyone needs daily, weekly and monthly reports. | Each cadence is optional. On-demand service is legitimate. No reports does not mean permission for hidden monitoring. |
| A plausible hypothesis is enough to change the plan. | A hypothesis justifies an investigation when useful. A dependent plan change needs adequate evidence and authority. |
| Improvement proves the suggestion worked. | Delivery, execution and observed change are separate records. Coincidence does not establish causation. |
| The intermediary can safely omit anything to save attention. | The Chief of Staff applies the participant's agreement and documents meaningful deferral. Important uncertainty is not erased to shorten a message. |
| Apple Health contains everything the team might need. | It was a preferred starting point, not verified coverage. Inspect available fields, source, units, dates and quality; degrade honestly when absent. |
| A connected account grants permission for all use and sharing. | Permission is scoped to purpose, data, recipients, retention and actions. Technical access and permission are different. |
| A document mentioning a platform proves an integration works. | Host capabilities must be observed in the actual installation. Historical references to other products called “Dot” are not capability evidence for this host. |
| The conceptual approval proves final owner acceptance or agent quality. | The earlier proposal had limited initial acceptance. This release enables a pilot; participant acceptance and real-host outcomes still require testing. |

## Questions converted into participant onboarding

These were open in the source design. They are resolved per participant, not by imposing one universal answer in the repository.

| Decision | Useful question or discovery | Safe behavior until settled |
|---|---|---|
| First useful result | What would make this help worthwhile now? Reuse an explicit recent answer when permitted. | Explain the service or run synthetic examples; do not assign a health goal. |
| Available context | What relevant sources can the host actually access, with what permission? | Distinguish unconnected, unavailable, partial and available sources. |
| Data scope | Which metrics or fields, purpose, recipients and retention are allowed? | Do not ingest or delegate private data outside an agreed scope. |
| Style of help | One-off answer, selected ongoing support, optional reviews? | Do not start scheduled monitoring or reminders. |
| Attention | Preferred language, channel, local timezone, quiet times and frequency? | Respond to the current request; do not invent a standing notification schedule. |
| Action authority | May the host only suggest, or also perform specific external actions? | Prepare a concrete proposal; use actual action authority before execution. |
| Concerning information | What supported human route is available, and what does the host actually support? | Preserve limits and direct urgent concerns toward appropriate human help; never claim automatic emergency handling. |
| Retention and continuation | Which private state can be stored and resumed, for how long? | Explain the host's real limits; do not claim durable memory or deletion beyond observed capability. |
| Pilot success | Which result would the participant judge useful, and what attention cost is acceptable? | Record a proposed criterion for review; do not equate message count with benefit. |

Ask only questions that change the current decision, after inspecting existing authorized context. Valid consent for the same scope need not be requested repeatedly. New purposes, recipients or external actions require the corresponding authority. Existing permission can be revoked.

## Seven source scenarios, translated into pilot expectations

| Scenario | What the pilot must demonstrate | Failure to avoid |
|---|---|---|
| 1. Recent sleep data and a busy upcoming day | Combine sufficiently reliable, permitted evidence with the participant's actual priority; propose only an appropriate next step. | Assume short sleep from calendar alone, prescribe food or treatment, edit the calendar without authority, or expose health details to a helper. |
| 2. Calendar only | Offer useful help within known scheduling context and explicitly limit unknown wellbeing claims. | Infer sleep, mood or physical state from missing sensors. |
| 3. Changed activity and physiotherapy entries | Keep observations separate from a possible recovery explanation; seek useful authorized context and revise when corrected. | Diagnose an injury, infer medical clearance, or change a plan solely from the hypothesis. |
| 4. Possible increased work pressure | Consider alternative explanations and ask the Chief of Staff for existing relevant context before interrupting the participant. | Diagnose mental health from tone or a crowded calendar. |
| 5. A withheld suggestion, or unknown execution | Track delivery separately from execution; use deferral reasons and preserve unknowns even if observations later improve. | Resend the same suggestion repeatedly or claim proven impact. |
| 6. Relevant previous training is unknown to another helper | Transfer the minimum useful, authorized context and surface conflicts through the manager and Chief of Staff. | Broadcast all logs, create an agent per human coach, or replace professional judgment. |
| 7. A repeated pattern near certain meetings | Check comparability, repetition, context and other explanations; present an association with its uncertainty. | Claim causation or impose one standard intervention. |

These scenarios test reasoning and boundaries. A local deterministic harness can test data validation, consent checks and state transitions. Real host runs are required to evaluate dialogue, meaningful delegation and judgment. See [acceptance tests](acceptance-tests.md) for execution and scoring.

## New engineering choices versus inherited requirements

Portable Markdown instructions, machine-readable contracts, a local reference harness, synthetic fixtures and automated package checks are engineering choices for this release. The source design did not mandate a particular framework, JSON format, model, service provider, database or schedule.

The participant-facing commissioning request was further clarified on 7 November 2026: the package must specify each agent's goals, responsibilities, tasks, skills and access in enough detail for Dot to build the team, manage it, assign work and collect reports. That explicit current requirement extends the older conceptual design into an operational pilot. It does not establish that Dot already has a working creation API or that the original design selected fixed task states.

| Current requirement | Operational pilot interpretation | Evidence needed |
|---|---|---|
| Complete agent specifications | Each role has a mission, accountable result, task boundaries, skills, minimal input/access, report expectations and completion criteria. The [team blueprint](../agents/team-blueprint.json) makes the mapping inspectable. | Role and blueprint validation; the host loads the corresponding role and skill instructions. |
| Dot builds and manages the team | The host checks actual capabilities, binds the Chief of Staff role, creates supported role instances, records real identifiers and distributes only the instructions and context each needs. | Actual instance creation results; explicit virtual-role mode when creation is unavailable. |
| Dot assigns tasks and collects reports | The host and manager use bounded task assignments, expected reports, review, correction and closure. The [orchestration playbook](orchestration-playbook-fa.md) explains the work cycle. | A task assignment, member report, reviewer decision and observed final state in a synthetic host run. |
| Work survives a supported restart | The reference runtime provides a private task ledger; the host uses its actually available private persistence and resumes only valid scoped tasks. | Local persistence tests and a separate host restart exercise. |

[Task records](../templates/task-contract.json), [member reports](../templates/task-report.json), [instance registries](../templates/agent-instance-registry.json) and ledger state transitions are new engineering contracts chosen to satisfy this request. They coordinate work and preserve accountability; they do not prescribe one clinical or lifestyle decision, require all roles for every request, or create access beyond the participant's agreement. A report that has been received still needs review, and task closure does not prove that a suggestion reached the participant, was performed, or caused an improvement.

Where a host supports genuine subagents, it can create the role instances and supply their relevant instructions and scoped context. Where it does not, it can perform the same role responsibilities in one conversation and disclose that limitation. “Role simulation” must not be reported as proof that independent agents, background jobs or persistent storage exist.

The public package cannot itself connect a participant's Apple Health account, grant access to a calendar, install private memory, or ensure a host will run tomorrow. Those require the participant's environment and observed integration receipts. The development handoff specifies the implementation boundary rather than disguising missing integration as success.

The next empirical question is whether the three-role arrangement provides better context preservation, answer quality and follow-through than a manager with one generalist. Compare the same scenarios, record duplicate work, latency, cost and user preference, and change the arrangement only for a demonstrated reason. More agents are not evidence of better help.
