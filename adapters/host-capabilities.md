# Host capability and provisioning contract

For ChatGPT Dot use [the executor route](chatgpt-dot.md) and [INSTALL](../INSTALL.md). Discover the actual session's tools before asking for information already available. Do not inspect personal accounts or health records merely to prove a capability.

| Capability | Required evidence |
|---|---|
| Source entry | Read current instructions and record version/commit |
| Executor | Actual bounded Work/Codex execution result; a drafted task is insufficient |
| Private persistence | Authorized outside-repository write/read and resume; explain ACL/disk limits |
| REST/local MCP | Authenticated operation; for MCP actual SDK initialize/list/call roundtrip |
| Native roles | Host creation ID/receipt, instruction attachment and synthetic acknowledgement |
| Media | Actual permitted vision/transcription result, not a URL placeholder |
| Channel | Authorized send and actual channel receipt; reading/acting remains separate |
| Scheduler | Actual job creation/readback, timezone, next run, owner and cancellation route |
| Phone | Device setup plus actual upload and scoped durable read; synthetic receipt is insufficient |
| Mirror | Authorized write/readback, correction/deletion and concurrency recovery |

Record individual `unknown`, `unavailable` or `verified` capabilities. MVP verified configuration requires `receipt_ref` and timezone-bearing `checked_at`; these are host attestations, not independently authenticated proof. Native configuration requires a real `instance_id` and `receipt_ref`. Recheck changed environments and stale evidence.

## Provisioning

1. Load [catalog](../agents/registry.json), [blueprint](../agents/team-blueprint.json), relevant role/skills and current participant scope.
2. Inspect context inheritance and tool exposure. If a worker inherits sensitive history or broad tools, disclose the actual route and resolve missing authority before transfer.
3. Activate only needed responsibilities. Use supported native creation with actual receipts, or explicitly virtual role perspectives. Never call prepared definitions running workers.
4. Give minimum context, bounded objective, acceptance and no extra authority. Keep specialist credentials separate from host credentials. Creation, acknowledgement, task claim, report and review are distinct evidence.
5. Review another responsibility's report before closure. Record delivery independently. On scope change/pause, stop actual workers and address exported copies as well as local state.

Virtual roles and CLI output share the invoking host's visibility. A recipient label does not hide data from that host/provider. If that exposure is denied, use a genuinely isolated authorized route or do not transfer the data. Category checks are not row-level task sandboxes; free-text objectives/reports also require minimization.

## Execution and fallback

MVP tools use private Python, authenticated REST or local MCP stdio. ChatGPT web does not read local MCP configuration or automatically import OpenAPI tools. Remote authenticated MCP/OAuth is a separate pending adapter; sensitive public MCP must not use no-auth as a workaround.

The API's in-process ticker produces reminders while the process runs. [host_tick.py](../scripts/host_tick.py) collects private jobs and applies actual results; it supplies no model/channel API and registers no recurring job. Preserve unresolved private job files until reconciliation, respect leases, and remove them under retention after processing. Confirmed `not_sent` permits retry; timeout alone does not.

Conversation-only support may remain useful, but is not successful MVP installation. State the missing capability and concrete next owner. Do not invent APIs, registered plugins, cloud persistence, schedules or purchases. [Runtime](../docs/runtime.md) distinguishes the SQLite MVP from legacy JSON commands.
