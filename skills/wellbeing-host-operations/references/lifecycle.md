# Host lifecycle procedure

These are host-neutral operations. Map each to tools actually advertised in the current
environment. Do not invent `dot.spawn`, a Grok API or unsupported vendor commands.

| Step | Action | Required evidence |
|---|---|---|
| Inspect | Discover available tools and context inheritance | Capability state and reason. |
| Prepare | Read role blueprint, selected skills and current scope | Package commit/version plus loaded paths/hash. |
| Create | Call actual native creation tool, or select explicit virtual mode | Actual ID/receipt, or `virtual:<role>` with no process claim. |
| Prove readiness | Send harmless synthetic mission/scope/reporting task | Actual acknowledgement; fix mismatches. |
| Scope | Select necessary tool/data access using current charter | Concrete source/purpose/recipient/expiry and actual host exposure. |
| Assign | Create task contract; send minimum authorized packet | Task ID, instance ID, dispatch receipt; packet alone is not sent. |
| Collect | Obtain role result for that task | Task-linked report, evidence, uncertainty and action receipts. |
| Review | Manager/CoS check acceptance and consequences | Per-criterion pass/fail/unknown with rationale. |
| Recheck | Request one specific correction when needed | Linked revision and change in evidence/result. |
| Verify | Inspect deliverable or outcome instead of trusting wording | File/tool/readback/evidence appropriate to the acceptance condition. |
| Close | Record outcome, delivery state and any remaining owner | Closed reason or explicit blocked/cancelled/expired state. |
| Resume | Validate checkpoint, scope and instance existence | Actual status and preserved current choices. |
| Cancel | Stop affected work/schedules through available controls | Cancellation receipt, or explicit termination-not-verified. |

## Host task states

Use semantic states appropriate to the host; do not confuse them with a CLI enum.
The package templates use `draft`, `ready`, `assigned`, `acknowledged`, `working`,
`blocked`, `result_ready`, `review_requested`, `verified`, `closed`, `cancelled`, `expired`.

Normal path: draft → ready → assigned → acknowledged/working → result_ready → verified
→ closed. A role response may combine acknowledgement and completion, but its evidence
must still establish both. A result can return to review_requested/working. A missing
dependency blocks the task; a cancellation or expiry prevents further dispatch. Receipt
loss does not justify inventing a state transition. Store timestamps when actually observed.

Suggested task-ID pattern: a private unique identifier, independent of the participant's
name or health information. Reuse the same ID for a retry of the same operation; use a
revision ID for corrected deliverables and preserve the earlier basis as authorized.

## Task acceptance

Good: “Answer whether these two recorded periods are comparable; cite source/coverage,
preserve missingness and distinguish planned from performed events.”

Weak: “Analyze everything perfectly.”

Good: “Offer feasible alternatives for the participant's already-selected routine using
their stated time limit; identify any decision still needed; do not create reminders.”

Weak: “Improve wellbeing.”

Checking a substantive report means checking the specific evidence and meaning of its
claim, not only that it contains headings. Agreement between two language-model roles
does not validate truth. When evidence is unavailable, mark the criterion unknown and
limit the answer/action accordingly.

## Least access by task

Manager usually needs goal, scope, task states, selected findings and decision needs.
Analyst needs the selected observations plus definitions/provenance/coverage relevant to
the question. Coach needs the chosen goal, reliable findings and practical constraints.
CoS needs enough to judge wider-life fit and present the result; actual tool exposure
must be disclosed. Do not attach credentials or full raw history to a task packet.

If a host cannot implement technical restrictions, state that limitation. Behavioral
instructions and logical role scopes remain useful but are not a security boundary.
Never claim least-privilege enforcement just because a prompt says “only read X.”

## Skill lifecycle

Trigger: repeated or material task gap observed with evidence. Prefer improving or
selecting a skill for an existing responsibility before adding a new role. Define the
skill's purpose, inputs, outputs, boundaries and success examples. Use authoritative
sources when external technical/domain facts are needed. Never include private participant
records, credentials or clinical conclusions as training examples. Test with synthetic
cases, record actual results, attach the version/hash to relevant instances and retain
rollback metadata. A tested synthetic example is not proof of clinical competence or
universal live-host compatibility. Installation requires actual supported host operations;
otherwise record instruction attachment only.
