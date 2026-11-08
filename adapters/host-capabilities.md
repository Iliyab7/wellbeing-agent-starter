# Host capability and provisioning procedure

**2026-11-08 memory extension:** Read [shared-memory responsibilities](../docs/shared-memory/README.md).
Manager designs/maintains participant-specific Sheets memory and assigns logging duties;
all roles register authorized data, work, exchanges and source-linked outputs. Check actual
read/write/scheduling/intake capabilities; downloading this package does not activate them.
On resume, recover the active structure, valid authority, findings and open tasks. Local and
conversation fallbacks remain available; no universal tab layout is prescribed.

This is a portable procedure, not a Dot/Grok SDK or API integration. Check the actual
session's available tools. Use [the capability template](../templates/capability-report.json)
as a private record. Do not probe personal accounts or fetch health data to prove a capability.

| Capability | Acceptable evidence | What the package alone does not prove |
|---|---|---|
| Read source | Successfully read this version's required files, recording version/commit | Seeing a repository name does not mean its instructions were loaded. |
| Execute code | A harmless local command succeeded in a controlled workspace | A chat/code block is not an execution. |
| Private files | Verified write/read in an authorized location outside the public repo | File existence does not prove encryption, backup or durable retention. |
| Durable continuity | Documented storage controls plus verified persisted checkpoint | Chat memory, workspace persistence and cross-chat identity are not interchangeable. |
| Independent agents | Successful native spawn with returned IDs and a synthetic response | A role manifest, prompt or virtual role is not a separate running agent. |
| Scheduling | Successful job creation/readback: ID, timezone, next run, delivery target | Planning a date or running a local CLI once is not a scheduled service. |
| Data connector | Available tool/access metadata and authorized read result | A product name or connected account is not permission for every data type. |
| Deletion/export | Actual operation on requested scope with verified outcome | Deleting local state does not erase provider logs or received messages. |

## Choose and record the mode

Use `conversation`, `workspace` or `native-agents`, as defined in
[CHAT-STARTER.md](../CHAT-STARTER.md). Capabilities can be mixed: a host may have agents
but no scheduler, or files but no durable storage. Record individual limits rather than
treating mode as a guarantee. Provide the participant a short plain-language statement.

Host modes and CLI flags use different names deliberately:

| Host mode | Optional CLI preparation | Meaning |
|---|---|---|
| `conversation` | None required | Work directly in the current chat. |
| `workspace` | `python -m wellbeing --home PRIVATE_DIR team --mode inline` | Prepare a role manifest for one host; no agents are spawned. |
| `native-agents` | `python -m wellbeing --home PRIVATE_DIR team --mode native` | Prepare a native-role manifest after authority checks; the host must still use its actual spawn tools. |

Replace `PRIVATE_DIR` with the participant's actual authorized private state directory.
Both CLI modes return preparation evidence only (`manifest_only`), not running processes.
Do not pass host labels such as `conversation` or `native-agents` as CLI mode values.

## Provision native roles when supported

1. Read the [catalog](../agents/registry.json) and full starter. Prepare empty role
   definitions before processing private data. Host CoS remains the one user-facing interface.
   Load CoS's [host operations skill](../skills/wellbeing-host-operations/SKILL.md) and
   [complete team blueprint](../agents/team-blueprint.json). Use the
   [instance receipt template](../templates/agent-instance-registry.json),
   [task contract](../templates/task-contract.json) and
   [report contract](../templates/task-report.json) as private host records.
2. Inspect the spawn API's context inheritance and tool scopes. Use minimal fresh context
   when possible. If full history will be inherited, avoid sensitive delegation until that
   exposure has appropriate participant consent or use virtual roles instead.
3. Attach only the relevant role file, its named skill module(s), the common boundaries,
   and a scoped task. Do not copy unrelated personal context or grant all host tools.
4. Create Manager as needed, then Analyst/Coach only for relevant work. Record each actual
   ID, creation result, instruction version, permitted tools, scope and lifecycle state.
   A returned ID is creation evidence, not evidence that the assigned analysis completed.
5. Send a harmless synthetic acknowledgement task: state responsibility, user-facing
   interface and data boundary. Correct mismatches before sending participant context.
6. Obtain participant consent for actual purpose/source/recipient/retention. Verify each
   packet's scope immediately before real transfer. The local CLI's `team` command prepares
   a manifest and `packet` prepares content; neither calls the host's spawn/send API.
7. Collect actual results and distinguish acknowledgement, completion, delivery and reading.
   Never infer successful work from a manifest or spawn receipt. Use role IDs for continuation
   only while valid. Terminate/retire no-longer-needed native tasks where the host permits it.
8. On revocation/correction/pause, invalidate affected pending context and stop active work.
   Explain any unavoidable already-shared copies and actual host deletion limits honestly.

If the host cannot restrict tools or contexts, that is an explicit pilot limitation.
Do not advertise security isolation. The reference runtime validates local records and
packets; it cannot enforce behavior of a remote model after transfer.

Virtual roles share one conversation, and a host executing the CLI receives its output.
An `analyst` recipient label does not hide packet contents from that host/CoS or its
provider. Include the actual processing host in the participant's understanding of
recipients. If CoS is excluded from given data, do not run that data through CoS-visible
tools/chat; use a genuinely isolated authorized worker or stay with permitted/synthetic data.

## Scheduling and source connections

Only set these up if the participant chooses them and the host has actual tools. Show
the purpose and concrete scope, use existing valid authority, and verify the resulting
operation. Keep a cancellation/revocation route. Unknown write result requires readback
before retry. No scheduler means on-request return; no connector means a narrower task
or authorized manual data. Do not invent platform APIs, install random plugins, create
paid infrastructure or request passwords as a workaround.

For the local reference runtime, follow [docs/runtime.md](../docs/runtime.md). Its policy
and state files are distinct from the informal host templates in `templates/`.
