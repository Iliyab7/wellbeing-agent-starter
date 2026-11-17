# ChatGPT Dot — autonomous setup through an executor

The target is the participant's ChatGPT Dot. No private profile identifier belongs in this public package. Sharing the repository URL for setup leads directly to [INSTALL.md](../INSTALL.md); do not request a second prompt or make the participant choose a technical transport.

## Supported route and evidence

Official [Dot computers/apps guidance](https://learn.chatgpt.com/docs/dots/computers-and-apps.md) describes Dot's cloud computer/browser, continuity and ability to start cloud Work/Codex threads. Local computer access is separate and depends on the connected computer remaining online with the app open. These documented capabilities do not establish this account's available tools or durable server hosting.

1. Read INSTALL and inspect actual session tools, connected execution and existing private setup. Reuse current authority and state.
2. If direct execution is unavailable, start a scoped Work/Codex task through an actual available tool. Supply the repository/version, install objective, private-state requirement, allowed actions and concrete return evidence. No invented thread API or creation receipt.
3. Executor installs/resumes the complete checkout, tests synthetic state, uses private Python/REST or supported local MCP, and returns a sanitized result. Keep tokens, database contents and pairing links out of general task reports. Give phone links only to the authorized participant.
4. Verify continuity and service hosting separately. A thread that ran once is not an always-on service. Continue independent setup if a device/channel grant is pending.
5. Run only relevant wellbeing responsibilities. CoS receives ready sections/links and decides attention. Native role execution needs IDs and receipts; otherwise use explicit virtual responsibilities.

The actual private account could not be inspected during coordination because browser access was challenged. Live account execution, channels, schedules and service persistence remain unverified. If a required capability is missing, explain the single concrete connection/enablement step in ordinary language while continuing independent work. Do not ask for passwords or present a menu of infrastructure stacks.

## Local tools are not web plugins

[ChatGPT MCP guidance](https://learn.chatgpt.com/docs/extend/mcp.md) distinguishes remote plugins from local Codex configuration. Dot web does not read `mcp.private.json`; this service's `/openapi.json` is not automatically imported as ChatGPT tools. Current code provides local stdio MCP and authenticated REST for an executor.

A direct remote plugin requires a separately implemented authenticated MCP adapter. Official [remote MCP guidance](https://developers.openai.com/api/docs/guides/custom-mcp-server.md) describes SSE/streaming HTTP and supported authentication. Follow [plugin OAuth guidance](https://developers.openai.com/plugins/build/auth.md), including PKCE S256, protected-resource/authorization metadata, trusted redirects and resource audience validation. Do not assume arbitrary Bearer import into ChatGPT. Never publish sensitive-data MCP without authentication.

Pending implementation should add `wellbeing/remote_mcp.py`, a reviewed OAuth integration module such as `wellbeing/oauth.py`, `tests/test_remote_mcp.py` and `tests/test_oauth.py`. They must test identity-to-participant/role binding, scope enforcement, invalid audience/redirect rejection, revocation and real ChatGPT discovery/calls. These are proposed future files, not existing features. Do not make this adapter a prerequisite for the executor route.

The root `plugin.json` is portable instruction packaging using the [agent plugin schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), with skills discovered from `skills/` by compatible consumers. It is not proof of installation, publication or a registered ChatGPT plugin.

## Installation receipt

Return observed version/revision and private execution/storage status; actual Work/Codex or native-instance receipt where available; synthetic checks; external HTTPS/restart evidence; phone intake event/receipt; selected channel and scheduling evidence; remaining human step and owner. Capability configuration fields are host attestations, not independent platform verification. Record secrets and detailed evidence only in the authorized private store.
