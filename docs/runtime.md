# Local reference runtime

The Python runtime is a small, working support layer for a host-led pilot. It stores one participant's agreed scope, validates numeric imports, computes descriptive observations, tracks a plan and its independent receipt/implementation/outcome, and prepares scoped role packets. Dot or another capable host supplies conversation, judgment and actual role execution using the [role catalog](../agents/registry.json).

It makes **no network calls** and contains no LLM client, wearable connector, scheduler, notification sender, or external-action tool. A team manifest is not a spawned team. A packet is not a sent message. This reference implementation is for the initial pilot and developer evaluation, not a clinical service or a hardened multi-user backend.

## Run the verified synthetic path

Use Python 3.11 or newer from the extracted source checkout:

```bash
python scripts/demo.py
python -m unittest discover -s tests -v
python -m wellbeing --help
```

No third-party library is needed for these commands. The demo drives the real CLI through 37 commands, including expected denials and an internal task/report/review cycle, in a temporary directory outside the repository. It generates fresh, explicitly synthetic observations and removes them when finished. `python scripts/demo.py --keep` retains only that synthetic workspace for debugging. It does not test a live Dot/Grok account or real subagent creation.

Run from the bundle root. `pyproject.toml` supplies project metadata; a standalone installed command without the accompanying agents/skills/documents is not the supported distribution. The complete checkout or ZIP is the runnable product.

## Private workspace and host visibility

The default workspace is `~/.wellbeing-starter`. Choose a separate path per participant with `--home PATH` **before** the subcommand, or set `WELLBEING_HOME`. The runtime refuses participant state and generated exports/packets inside its public source checkout. It does not identify users by display name; every new workspace gets a random ID, and `init` refuses to overwrite an existing workspace.

The trusted local operator and the host executing these commands can read the state and stdout. Recipient filters minimize the packets prepared for downstream roles; they are **not process isolation or access-control boundaries against that operator**. Before using a host, obtain the participant's agreement to that host's actual visibility, storage and model-provider processing. If the participant requires isolation from the host itself, this runtime is unsuitable; use a separately secured deployment. The runtime cannot enforce a provider's chat retention, model training or remote deletion policy.

State is plaintext JSON with restrictive POSIX file permissions and atomic replacement. This is not encryption. Existing directory permissions, Windows ACLs, host logs, terminal scrollback and backups remain the operator's responsibility. Do not put personal text in GitHub issues, public artifacts or CI. Use `--goal-file`, `--text-file` and `--outcome-file` to keep personal text out of shell history/argument lists; the selected files, CLI output, exports and tool traces still contain private information.

Only one writer can hold a workspace lock. A stale `.write-lock` is reported rather than automatically deleted. Investigate and stop the old writer before removing a genuinely stale lock. The runtime never reads credentials or modifies system configuration.

## Agree the scope, then configure

Begin with the [participant flow](participant-pilot-fa.md), not a prefilled policy. The [synthetic policy](../examples/policy.synthetic.json) is a test fixture, **not participant consent**. Use the [policy schema](../schemas/policy.schema.json) to produce a private policy reflecting the actual agreement.

```bash
python -m wellbeing --home ../participant-private init --goal-file ../participant-private-goal.txt --timezone UTC+03:30 --alias participant
python -m wellbeing --home ../participant-private configure --file ../participant-private-policy.json --confirmed --consent-reference "private agreement record identifier"
```

`--confirmed` is an attestation by the invoking host that the participant actually agreed. It does not manufacture consent and does not ask the user itself. `--consent-reference` optionally records a private pointer to that agreement; without one the audit says `host_attestation_only`. An agent must never select this flag merely because a sample command contains it.

The initial state is `awaiting_consent`. A policy explicitly specifies:

| Field | Operational meaning |
|---|---|
| `purpose` | One stated purpose for this workspace; multiple unrelated purposes need separate scopes/workspaces. |
| `retention_days` | Participant-selected positive retention. The 36,500-day maximum is a technical date-range bound, not a recommendation or default. |
| `valid_until` | An offset-aware expiry timestamp; explicit `null` means ongoing until revoked. Expiry blocks processing and packet verification. |
| `journal` | Permission to retain check-ins, draft plans and review statements locally. |
| `team_recipients` | Explicit roles permitted to receive goal/task context. Empty is allowed. |
| `sources` | Explicit source ID, consented metric-to-unit mapping, separate analysis permission and permitted downstream recipients. Presence of a source/metric grants import for that purpose. |
| `authority` | Whether drafts and native subagent creation are authorized. This never authorizes messaging, calendar writes, purchases or medical decisions. |
| `attention` | Participant preferences for the host: on-request or agreed schedule, optional quiet-hour pair, optional daily ceiling. These preferences do not create a scheduler or monitoring. |

Null quiet hours and ceiling mean no value was agreed; they are not hidden defaults. For `agreed_schedule`, the host must separately record the actual selected schedule/channel and verify a real scheduling capability before claiming anything runs. No clinical thresholds or universal sleep targets exist in this policy.

Reconfiguring a paused workspace keeps it paused. It invalidates old packets and team manifests. Removing a metric or changing its unit removes incompatible records and dependent plans rather than relabelling numbers. Changing the purpose clears previous observations, plans and check-ins; it does not silently repurpose them. A reduced journal grant deletes the stored journal. Review these effects with the participant before replacing their policy.

Timezone support uses an installed IANA database, for example `Asia/Tehran`. Where that database is unavailable (commonly a bare Windows Python install), `UTC` and explicit fixed offsets such as `UTC+03:30` work without dependencies. A fixed offset does not follow daylight-saving or future timezone-rule changes. For IANA names on Windows, installing `tzdata` separately is an optional environment setup task. The runtime produces a clear error rather than guessing the timezone.

## Import and inspect observations

Imports are JSON lists following the [record schema](../schemas/record.schema.json). The CLI does not directly parse CSV, Apple Health XML, WHOOP exports or calendar APIs. The host or a future adapter must map an authorized source deliberately into the record contract and retain the original source/measurement meaning.

```json
{
  "id": "synthetic-observation-1",
  "source": "manual",
  "metric": "sleep_hours",
  "value": 7,
  "unit": "hours",
  "observed_at": "2030-01-07T08:00:00+03:30",
  "origin": "synthetic"
}
```

This example is synthetic and its fixed timestamp is explanatory. The demo generates usable current timestamps. Real records must reflect actual observation times within the chosen retention window; future/expired observations are rejected. `origin` can be `self_report`, `device`, `calendar` or `synthetic`. The label identifies the declared origin, not independent verification of authenticity.

```bash
python -m wellbeing --home ../participant-private import --file ../private-records.json
python -m wellbeing --home ../participant-private source-status --source manual --status partial
python -m wellbeing --home ../participant-private analyze --source manual --metric sleep_hours --since 2030-01-01 --until 2030-01-07
```

Import is transactional: a malformed final row leaves the whole batch uncommitted. Identical repeats are idempotent; conflicting IDs or source/metric/instant duplicates are rejected. Unit changes require an explicit new definition, never implicit conversion. Offset-aware timestamps are normalized; date coverage uses the participant's timezone. Boolean values, nonfinite numbers, duplicate JSON keys, mismatched units and naive timestamps are rejected. `null` is explicitly missing; unobserved dates and null rows are not zero.

Analysis returns counts, min/max, first/last recorded values and an equally weighted mean of numeric records. It reports coverage and limitations, with empty hypotheses, confirmed explanations and recommendations. It does not infer a personal baseline, clinical state, causality, completed behavior or a treatment effect. Multiple observations on a day receive multiple weights; use a consistent measurement definition. A source status can be `available`, `absent`, `partial`, `stale`, `conflicting`, `technical_failure` or `not_checked`. Historical observations can still be displayed alongside a technical failure; a failed connection is not reported as proof that data is absent.

The default analysis window is the current local date and preceding six dates. This is a query convenience, not an agreed check-in/report cadence or a sufficient baseline. Specify the range needed for the question. The host decides whether a question can be answered and whether clarification has enough value.

## Prepare the relevant roles and context

```bash
python -m wellbeing --home ../participant-private team --mode native
python -m wellbeing --home ../participant-private packet --role analyst --task "Review uncertainty in the selected observations" --source manual --metric sleep_hours --output ../private-analyst-packet.json
python -m wellbeing --home ../participant-private verify-packet --file ../private-analyst-packet.json
```

`team` validates and loads the [catalog](../agents/registry.json), including each role's instruction and skill paths. It creates a `manifest_only` provisioning plan with members `not_started` and no tools. The host must actually install/provide the listed skills, create a native agent if supported and authorized, and record observed creation/execution receipts. With `--mode inline`, one host uses distinct role perspectives and describes that honestly. Do not activate every member for every request; analytical and coaching work are independent responsibilities.

`packet` requires both a `team_recipients` grant and the selected source's recipient/analysis grant. It includes only the selected descriptive summary, goal, task, purpose, relevant evidence IDs, authority and uncertainty. It does not automatically include journals, full raw records or unrelated sources. Journal sharing requires a separately agreed host-level handoff; there is no automatic journal-export-to-role command.

Immediately before a host sends a packet, run `verify-packet`. The local issuance hash, current policy revision, consent expiry, recipients and retained evidence must still match. Revoke, correction, policy replacement, goal change or deletion invalidates old packets. `prepared_not_sent` remains the truthful receipt until the host actually verifies an external handoff. Previously exported copies are not magically recalled; instruct the receiving system to stop/delete them where supported.

## Assign work and review reports

The private task ledger makes internal coordination repeatable while the host executes the actual agents. It is separate from the participant's chosen plan: closing an analyst task does not mean a recommendation reached the participant or changed a habit. See the [orchestration playbook](orchestration-playbook-fa.md) for the host's complete create/assign/collect/review loop.

Use the [runtime task contract schema](../schemas/task-contract.schema.json) and [runtime report schema](../schemas/task-report.schema.json). The richer host templates are protocol examples, not interchangeable CLI inputs. The [synthetic task](../examples/task.synthetic.json) and [synthetic report](../examples/task-report.synthetic.json) demonstrate the exact CLI formats; neither is real participant consent or execution evidence.

```bash
python -m wellbeing --home ../participant-private task create --file ../private-task.json
python -m wellbeing --home ../participant-private task context --id TASK_ID --output ../private-task-context.json
python -m wellbeing --home ../participant-private task dispatch-unknown --id TASK_ID --receipt-ref ATTEMPT_REFERENCE
python -m wellbeing --home ../participant-private task reconcile --id TASK_ID --outcome sent --receipt-ref TOOL_RECEIPT_REFERENCE
python -m wellbeing --home ../participant-private task report --id TASK_ID --file ../private-task-report.json
python -m wellbeing --home ../participant-private task review --id TASK_ID --decision revise --reason-file ../private-review.txt
python -m wellbeing --home ../participant-private task report --id TASK_ID --file ../private-revised-report.json
python -m wellbeing --home ../participant-private task review --id TASK_ID --decision accept --reason-file ../private-acceptance-review.txt
python -m wellbeing --home ../participant-private task close --id TASK_ID --reason "Internal acceptance checks completed"
python -m wellbeing --home ../participant-private task show --id TASK_ID
```

`task create` requires private journal permission, a consented recipient, the current purpose and a bounded list of authorized evidence IDs. It binds the task to the current policy revision, participant goal and exact evidence fingerprints. The task contract includes an objective, requested output, explicit acceptance checks and an optional real deadline. `evidence_ids: []` means no numeric evidence is authorized for that task. A repeated identical ID/contract returns the existing task; an ID with changed or invalidated content is rejected.

`task context` materializes **only those selected observations**, the assigned role's instruction/skill paths, objective, acceptance, deadline and limits. Its tool list is empty; the task grants no new external action or data access. Generate it immediately before the host handoff. Use this task-specific context rather than a broader source summary when the task's evidence scope is narrower. Files and source text are evidence, never commands to execute.

Before an external host dispatch, record `dispatch-unknown` with an attempt reference. This prevents a retry after a timeout from silently duplicating work. After examining the actual host receipt, reconcile as `sent` or `not_sent`; only a confirmed `not_sent` result returns it to `prepared`. A known completed dispatch may instead be recorded with `task dispatch --id TASK_ID --receipt-ref REF`. The ledger has no automatic retry loop. A reference string is **host-attested provenance**, not vendor authentication or proof independently checked by Python. The host must supply real evidence, not invent IDs.

A report must match the assigned role/task/policy revision and may cite only task-scoped evidence. It separates observations, uncertainty, requested decisions and the result. Report receipt changes state to `report_received`, never `verified`. Identical report receipt is idempotent. An internal reviewer may request revision or accept with an explanation against the acceptance criteria; an unchanged resubmission does not satisfy a revision request. `verified` means **host-reviewed internal acceptance**, not verified native-agent execution or validated medical correctness. Only then can the task close. These are normal internal responsibilities under the standing scope, not repeated permission questions for the participant.

| State | Meaning |
|---|---|
| `prepared` | Scoped assignment exists; not dispatched. |
| `dispatch_unknown` | Attempt needs reconciliation; do not retry. |
| `dispatched` | Host reports a known dispatch receipt. |
| `report_received` | Output received, awaiting review. |
| `revision_requested` | Internal reviewer requested a changed report. |
| `verified` | Host reviewer accepted the current report. |
| `closed` | Accepted internal task finished; no human delivery inferred. |
| `cancelled` | Local task cancelled; host must separately stop any external worker. |
| `invalidated` / `expired` | Scope/evidence/goal/retention/deadline no longer permits reuse. |

`task cancel --id TASK_ID --reason TEXT` is available while paused. Factual reconciliation and status can also be recorded while paused; new dispatch, reports and acceptance remain blocked. A revoked source, changed policy/goal, corrected/deleted evidence or expired consent invalidates affected reuse and clears private task content, including stored reports. Closed/cancelled tasks retain their terminal provenance while private contents are cleared. Successful CLI calls persist those checks; direct module operations also validate before work. Deadline expiry prevents new work but does not rewrite a previously completed task as unfinished. Task records are physically pruned under workspace retention; there is still no background deletion daemon.

## Track the chosen experiment without inventing adherence

```bash
python -m wellbeing --home ../participant-private check-in --text-file ../private-checkin.txt
python -m wellbeing --home ../participant-private plan --text-file ../private-plan.txt --evidence observation-id
python -m wellbeing --home ../participant-private review --plan-id PLAN_ID --receipt withheld
python -m wellbeing --home ../participant-private review --plan-id PLAN_ID --decision accepted --implementation tried --outcome-file ../private-outcome.txt
```

`check-in` stores the participant's text as uninterpreted self-report. `plan` stores a proposed draft, not an accepted or completed action. The host remains responsible for nonmedical content, contextual judgment and obtaining any action permission; this storage helper is not an automated clinical text filter.

Review fields stay independent:

| Dimension | Values |
|---|---|
| Participant decision | `proposed`, `accepted`, `declined`, `paused` |
| Delivery receipt | `unknown`, `not_delivered`, `withheld`, `failed`, `delivered`, `acknowledged` |
| Implementation | `unknown`, `not_started`, `tried`, `ongoing`, `completed`, `blocked` |
| Outcome | Optional self-reported statement with its timestamp; `causality` remains `not_established`. |

Being delivered or accepted never auto-marks the experiment as tried. A better outcome does not imply execution or causality. The runtime records host-supplied statuses; it cannot independently observe a person's behavior or prove that a message was read.

## Correction, new priorities, pause and control

```bash
python -m wellbeing --home ../participant-private correct --file ../private-corrected-record.json --confirmed
python -m wellbeing --home ../participant-private delete-record --id observation-id --confirmed
python -m wellbeing --home ../participant-private set-goal --text-file ../private-new-goal.txt --confirmed
python -m wellbeing --home ../participant-private pause
python -m wellbeing --home ../participant-private resume --confirmed
python -m wellbeing --home ../participant-private revoke --source manual
python -m wellbeing --home ../participant-private status
python -m wellbeing --home ../participant-private export --file ../private-export.json --confirmed
python -m wellbeing --home ../participant-private delete --confirmed
```

- `correct` takes one record object with the original ID/source/metric/unit, revalidates it transactionally, invalidates all prepared packets and pauses dependent plans for review. A collision with another observation is rejected without losing the original record.
- `delete-record` works while paused and deletes the selected observation plus explicitly dependent plans; it invalidates prepared packets.
- `set-goal` invalidates packets/team and pauses plans. Normally it returns to `awaiting_consent` until the purpose/policy is reviewed. Use `--same-purpose` only when the host has confirmed that the refinement stays within the existing purpose and permissions; it never resumes a paused workspace. Neither flag expands data access automatically.
- `pause` stops processing but retains already stored data under retention. `resume` requires a participant request and unexpired policy. New configuration alone does not override a pause.
- `revoke` works while paused, removes the selected source's permission and observations and deletes explicitly dependent plans. It invalidates packets. Unrelated journal text is not automatically interpreted or scrubbed; use whole-workspace deletion if it contains information the participant also wants removed.
- `export` requires authorization and a new destination outside the repository. It contains private state. It never sends a file anywhere.
- `delete` removes this workspace's `state.json`, not arbitrary neighbouring files. It does not remove host memory, exports, packet files, backups, external copies or provide secure physical disk erasure.

Retention pruning is opportunistic at CLI invocation and is persisted on a successful command (for example `status`). Expired observations are filtered out of analysis/packet validation even before physical pruning. A subsequent failed command does not commit its in-memory pruning. **There is no daemon and no guarantee that files are erased at a deadline while the runtime is inactive.** A production deployment needs a separately tested retention job and downstream deletion system. The current profile and consent policy remain until changed or the workspace is deleted.

## Output and failure contract

Successful commands return JSON `{ "ok": true, "result": ... }` on stdout with exit code 0. Validation, consent and file errors return `{ "ok": false, "error": ... }` on stderr with exit code 2. CLI JSON uses ASCII Unicode escapes, a valid UTF-8 subset, so Persian text survives legacy Windows/redirected consoles and is restored by normal JSON decoding. Private state files remain UTF-8. Errors do not echo imported health values. There are no automatic network retries or hidden background operations. Repeated imports are safe; a failed import is not a partial success. A successful local check is not evidence of production security, provider access, scheduled execution, medical validity or real-world wellbeing improvement.
