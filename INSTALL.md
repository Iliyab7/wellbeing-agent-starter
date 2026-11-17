# Executing assistant: install or resume now

A repository URL shared for setup is enough to begin reversible installation within the authorized workspace. Do not ask for another prompt or ask the participant to choose MCP versus API. Respect their current scope and the host's execution rules. Human steps remain necessary for device grants, account connection, purchases and missing material preferences.

## 1. Select an actual executor

For ChatGPT Dot follow [adapters/chatgpt-dot.md](adapters/chatgpt-dot.md). Use a bounded Work/Codex task capable of running this checkout, private Python operations, service REST or supported local MCP. Other hosts may execute directly when their tools support it. First inspect tools and existing private setup; do not overwrite or silently recover missing credentials.

Read [CHAT-STARTER.md](CHAT-STARTER.md), then relevant role instructions/skills. Record observed execution and private-storage receipts. Continue independent setup while a phone or channel step is pending. If execution cannot be reached, identify the smallest actual connection step; conversation-only help must remain labelled incomplete installation.

## 2. Bootstrap privately

Use the complete checkout on an authorized Python 3.11+ execution machine:

```sh
python scripts/bootstrap.py --install
```

Bootstrap installs pinned `requirements-mvp.txt` in a private venv and initializes/resumes `~/.wellbeing-mvp` by default. It produces private credentials, setup and local MCP configuration outside Git. Use `--home` for another authorized private location. The legacy `~/.wellbeing-starter` JSON workspace remains separate; no automatic migration is claimed.

Use the resulting venv Python and `setup.private.json` commands/environment. Preserve credentials on repeat bootstrap. A missing credential file beside an existing store requires deliberate recovery, not deletion or reprovisioning. Never print credentials into chat, logs or a public report. Protect OS permissions and disk/backups; SQLite encryption is not supplied.

Run synthetic checks separately from participant state:

```sh
python -m unittest discover -s tests -v
python scripts/demo.py
python scripts/mvp_smoke.py
```

Use the private venv Python in these commands. Missing optional dependencies or skipped integration checks must be reported. Full fresh dependency installation is distinct from the smoke script's repeated bootstrap.

## 3. Connect execution and durable service

Current interfaces are local MCP stdio (`scripts/run_mcp.py`) and authenticated REST (`scripts/run_server.py`). Import only the relevant local server configuration if the executor actually supports it. Alternatively the executor uses private Python/REST calls. Give specialists their own role credential and minimum context, never the complete credential bundle.

**ChatGPT web does not read `mcp.private.json` or automatically import `/openapi.json`.** That REST schema documents the executor interface. A public ChatGPT remote MCP/OAuth adapter is not implemented. Do not expose sensitive tools without authentication or advertise a registered plugin.

For phone intake use an existing authorized supervised machine and stable HTTPS reverse proxy/tunnel. Set `WELLBEING_PUBLIC_URL` to the actual base URL, repeat bootstrap with `--public-url` to update its private tool environment, and restart the service using the setup receipt. Verify `/healthz` externally and a controlled restart. Localhost, a persistent filesystem and a temporary task session do not establish an always-on reachable service.

The deployment owner must check proxy limits, secret/path logging, TLS, restart and protected backups. Do not provision paid hosting without applicable authority. Docker/Compose assets exist but their operation has not been verified. No blanket deployment success follows from their presence.

## 4. Prepare responsibilities and iPhone intake

Load Manager, Analyst, Coach and Emotional Companion instructions; activate only needed roles. Record native IDs/receipts if genuinely created, otherwise virtual mode. Check scope before every actual transfer. Task claims require host execution and reports; they do not create workers.

Use `wellbeing_pairing` or authenticated `POST /v1/pairing` after HTTPS is verified. Give the participant the private expiring setup link. They install Health Auto Export on the iPhone, choose trial/purchase, select categories/recipients/retention, grant Apple Health permissions and review/enable generated automations. Links contain an intake credential; keep them private. No fake signed `.shortcut` artifact is needed.

Explain category choices in ordinary language. All supported data is optional, never implied consent. The server enforces category scope; narrower metric selection is configured in HAE, not enforced by a server metric allowlist. Companion receives only State of Mind through standard pairing when selected; other selected recipients receive selected categories. Review those actual grants before confirmation.

Choose a bounded history window within selected retention, then Manual Upload. Generated defaults replay today/yesterday with a requested hourly cadence; this is not guaranteed iOS background timing. Check actual HAE version/settings, source selection, units and aggregation. Observe receipt plus event times and scoped readback before claiming phone intake. A transport receipt alone does not independently verify device origin. Test later incremental/replayed/delayed data and corrections; missing is not zero.

## 5. Deliver first value and chosen follow-up

Manager returns a concise ready answer/section with evidence, unknowns and next owner. CoS selects presentation time; team work handles any needed media preparation. Optional OpenGym use requires a configured reviewed bridge; use native links, never extract/forward licensed media.

Use existing host/channel capabilities for meal photos, voice and text. Persist only supported estimates through entry tools; retain message ID and stated occurrence time. Ask only consequential ambiguities. Use the same original role and ID for corrections.

Reminders default OFF. Configure participant-selected meal times, timezone, quiet hours and budget. The service's in-process ticker only produces queue entries while running. Register and read back a real host job for collection/delivery before claiming reminders are live. `scripts/host_tick.py --help` defines private collect/apply files when direct tools are unavailable; the host still performs real reasoning/channel calls. Protect and expire job/result files under the same retention scope.

Claim outbox, check current authority and lease, send through the actual authorized channel, then acknowledge with its actual receipt. Preserve idempotency keys where supported. Unknown sends require channel reconciliation before retry; queue acknowledgement is not reading or action.

Return a short component receipt: installed runtime/version, private persistence, service reachability/restart, native/virtual roles, actual phone event/receipt, media/channel capability, recurring-job evidence and open gaps. No real-phone, Dot, WhatsApp or deployment acceptance is currently established by the repository's synthetic tests.
