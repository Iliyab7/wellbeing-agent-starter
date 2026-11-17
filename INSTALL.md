# Agent: execute this when the user shares the repository URL

The user wants installation and first useful operation, not a repository summary. Treat sharing this package for installation as authorization for reversible setup within their workspace. Continue autonomously using available tools. Do not ask them to paste a launch prompt. Respect real account/device consent and costs.

## 1. Discover, persist, resume

- Read this file, `docs/mvp/host-contract.md`, and `agents/registry.json`.
- Find actual tools: shell/private files, durable HTTP service, HTTPS deployment, REST or MCP connection, native subagents, scheduler, existing user channel, vision, transcription, private Drive/Sheets/Notion if offered.
- Use actual calls and receipts; a product name is no evidence. Do not confuse unrelated products named Dot with this host.
- Reuse an existing private installation and permissions. Never overwrite its credentials or Health records on resume.
- Missing capabilities require the smallest concrete enablement step. A conversation-only simulation is NOT the installed MVP and must not be reported as such.

## 2. Install on the host's usable execution machine

Use an existing Python 3.11+ machine, or a participant-approved always-on service. Clone this repository if not already present. Read commands before execution. From its root:

```sh
python scripts/bootstrap.py --install
```

This creates the private state outside Git, a private venv, six credentials and five MCP configurations. The output prints paths/status, not secret values. Existing JSON reference state is left intact. After installation use the private venv's Python for all MVP commands.

If shell is unavailable but an authorized deployment/remote-execution tool exists, run the same package there. If neither exists, request the single missing execution connection; do not make the participant choose a stack. Gmail/Drive-only is a documented fallback to test, not evidence of installed API/scheduler.

## 3. Start and verify the private service

Use `setup.private.json`'s `serve_command` and `required_environment`. With no public URL, local operations can be tested but phone connection remains pending.

Use an existing approved HTTPS reverse proxy or persistent tunnel to make port 8787 reachable by the iPhone. Do not expose a raw unauthenticated database or start a paid service without its applicable authorization. See `docs/mvp/deployment.md`. Supply the stable HTTPS base as `WELLBEING_PUBLIC_URL`, then restart the service and probe `/healthz` externally. Request logs must not store pairing URLs or authorization headers.

Configure a process supervisor/restart policy on the actual server; a temporary tool session is not always-on hosting. Verify an intentional restart preserves records. Do not assume this user's laptop stays awake.

## 4. Connect tools and prepare the team

- Read credentials only into protected host connector/environment configuration, never chat or repository.
- If local MCP is supported, import the required server(s) from `mcp.private.json`. Each role has its own credential. Do not mount every specialist credential into an isolated specialist.
- For a remote host, register the service's `/openapi.json` and Bearer credential through its secure REST tool mechanism. REST tools are the remote MVP interface; no unauthenticated remote MCP is provided.
- Load Manager, Analyst, Coach and Emotional Companion role instructions and selected skills. Create independent workers with the host's actual native mechanism when available; otherwise explicitly use host-run role perspectives. Record actual instance IDs and creation receipts; don't manufacture background agents.
- Run bounded work via create → claim → report → review → close. Prepared is not dispatched, report_received is not verified, closed is not user delivery.

## 5. iPhone connection with minimal typing

- Explain briefly what data/recipients/retention the setup page offers. Reuse already valid user choices.
- Call `POST /v1/pairing` with host credentials. Privately give its expiring setup link to this participant.
- Participant installs Health Auto Export and chooses trial/Premium themselves. They open the setup page, select scope, open the generated export links, grant Apple's permissions, and enable automations.
- Do not buy the app, grant permissions or publish their setup link on their behalf.
- First use Manual Upload for a bounded history window. Poll `/v1/status`; acknowledge connection ONLY after observing an actual intake receipt and event times. Synthetic smoke data must use a separate store.
- Verify the generated HAE settings on this actual app version, especially headers, grouping, disabled-until-reviewed and source selection. Deep links were built from official docs; phone acceptance still matters.
- Native Shortcuts are optional for recovery/event triggers. HAE is the initial transport. Do not create unsigned fake `.shortcut` files; use Apple Shortcuts on the device/Mac when genuinely needed.

## 6. Meal reporting and low-interruption follow-up

Use existing knowledge; obtain only missing meal times/timezone/attention choices. Configure chosen breakfast/lunch/dinner reminders, quiet hours and budget through `/v1/config`; reminders default OFF until selected. Use current WhatsApp/host channel, not a new bot identity.

The service queues due reminders. The host MUST register a real recurring job (suggested every 5 minutes) that claims outbox, uses its actual channel tool, records the returned message receipt and acknowledges. If scheduling is unavailable, state reminders aren't live; API queueing alone is not notification delivery. Preserve the delivery ID as the channel idempotency key when supported; reconcile uncertain sends before retry.

When a photo/voice arrives, use actual host vision/transcription. Preserve source message ID and stated occurrence time; do not log guessed meal timing, ingredients, weights or calories as confirmed. Store through `wellbeing_record_entry`/`POST /v1/entries`. Ask only an ambiguity that changes useful help. Correct the same ID when the participant corrects it. Emotional notes use companion scope and minimized sharing.

## 7. First value and ready receipt

Manager uses real evidence to prepare a short Persian section or answer, with unknowns and next owner. CoS chooses how/when to present; it does not download fifteen videos or reconstruct analysis. Use OpenGym tools only when a real exercise task needs them (`docs/mvp/opengym.md`).

Finish with a concise receipt: runtime, public reachability, private memory, actual native/virtual roles, iPhone last event/receipt, channel, scheduler, meal flow and open gaps. Continue all independent setup even when one device permission is pending. Do not label the whole installation blocked merely because the phone step needs its owner.
