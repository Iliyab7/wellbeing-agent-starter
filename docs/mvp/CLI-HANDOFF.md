# Active delivery brief — 2026-11-17

## User's actual request

Deliver a substantial working MVP, not a roadmap-only or conversation-only starter. The participant gives ONLY the GitHub repository URL to Dot or another capable assistant. That host autonomously discovers instructions, installs/resumes, requests only genuinely necessary permissions, and begins useful work. It must accept Apple Health data originating from diverse gadgets through the participant's iPhone, support sleep/activity/workout data and any selected Health categories, persist private memory, run the Manager/Analyst/Coach team and fully define an Emotional Wellbeing Companion, support meal photo/voice reporting and breakfast/lunch/dinner reminders through the existing host/WhatsApp, integrate OpenGym where appropriate, and be simply installable from GitHub. User explicitly requests research-based what/why/how decisions, actual implementation and testing, and delegates remaining development/planning to the separate Codex CLI account in PROTECT_APP mode. No app-account substantive implementation after handoff.

## Meeting requirements (public-safe abstraction)

- CoS is attention gate and coordinator, not the downloader/transcriber of many exercise videos. Team delivers ready packets/links.
- A wellbeing section may feed the host's morning newsletter. Exact deadlines and 70/30 allocation were participant examples, not universal defaults.
- Build first on the participant's actual available phone/host, show usable execution, then version it.
- Initial bounded history import + incremental/replayed recent data. Corrections, duplicate input, delayed data and source failure must be explicit.
- Gmail transport was suggested as an initial fallback. API, Shortcuts and HAE are candidate mechanisms, not the core product.
- Memory is mandatory; Manager defines structure and role duties. SQLite private primary store is implemented; cloud mirrors must never be claimed without actual connector receipts.
- Host inference/vision/transcription/WhatsApp are used if available. Do not require a new LLM provider subscription. Native subagents only with actual creation receipts; otherwise explicit host-executed role perspectives, never pretend spawned workers.
- Do not require every domain to be a permanent agent or make all roles a mandatory pipeline.
- iPhone grants and purchase choice are human steps. No account access, always-on service or exact background run frequency can be invented from a repository URL.

## Baseline and already implemented work

Existing public repository is `Iliyab7/wellbeing-agent-starter`, v0.1.0. Preserve legacy Python reference CLI/tests. Current new code:

- `wellbeing/database.py`: separate SQLite primary state, participants, hashed role credentials, records/revisions, receipts, role entries, tasks, outbox and pairing.
- `wellbeing/service.py`: category-authorized HAE ingestion of 8 categories, dedupe/correction, scoped reads, role entries, meal checks, reminder tick, leased delivery queue, task lifecycle, packet and deletion.
- `wellbeing/api.py`: FastAPI API, OpenAPI, body limit, Bearer auth, temporary single-use iPhone pairing and explicit category choice, generated HAE deep links, in-process reminder producer.
- `wellbeing/iphone.py`: setup URL generator based on official HAE parameter docs (correct headers syntax and cadence now present).
- `wellbeing/mcp_server.py`: official MCP SDK v1.30 FastMCP stdio tools, local role-scoped service. Remote MVP uses REST/OpenAPI, no remote MCP yet.
- `scripts/bootstrap.py`: idempotent private install skeleton/venv, private credentials/config output; does not yet install dependencies because requirements file missing.
- `scripts/run_server.py`, `scripts/run_mcp.py`, `scripts/doctor.py`.
- `INSTALL.md` defines one-link executor workflow, root discovery still needs README/START-HERE/CHAT-STARTER updates.
- New companion role plus install/emotional-support/meal-intake skills. Registry/blueprint not updated yet.
- `tests/test_mvp.py`: service and HTTP tests all PASSED locally on 2026-11-17 with synthetic fixtures (39 reported, but APITests inherits service tests causing duplicate execution; fix this).
- `WORK-PLAN.md` is the initial dependency/acceptance plan.

No real iPhone data, pairing, background measurement, Dot native agents, WhatsApp send, live cloud memory or deployment has been verified. No service has been exposed publicly. No real credentials/health data are in repository.

## Tested dependencies and execution constraints

App coordinator created a dedicated external Python 3.14 venv with FastAPI 0.163.1, uvicorn 0.54.0, MCP 1.30.0, httpx 0.28.1, tzdata 2026.6. MCP latest 2.x renamed FastMCP; use MCP==1.30.0 for current implementation, or deliberately migrate and test. Provide pinned `requirements-mvp.txt`, preserve zero-dependency legacy tests via optional import skips as needed. Docker daemon is currently stopped; do not claim Docker image tested. Public artifact worker does not run tools; return allowlisted complete edits and proposed verification commands. Bridge/app performs actual tests and integration. Never claim testsExecuted when not executed.

## Work remaining: implementation and review

1. Review/harden new code; add missing behavior with meaningful tests. Check SQLite transaction/schema startup/restart, scope revocation and retention of derived copies, stale packets, leases and retry honesty, idempotency, malformed inputs, credential recovery, permissions and no data-in-log leaks. Health data stored unencrypted at rest; document OS/disk/volume access limits honestly.
2. Bootstrap: pin dependencies, smoke fresh install, don't silently recreate missing credentials, set public URL in MCP config where needed, add useful doctor/host capability receipts. Make pairing/status available through MCP too (currently only HTTP); refactor common operation instead of duplicating insecure logic.
3. Native agent role dispatch is host-led. Scope tasks and reports, enforce capability/receipt distinctions; no invented model training or clinical competence. Meal intake is through actual host media tools, no fake image recognition/transcription.
4. Outbox currently queues only meals/packets, not actual WhatsApp. A small executable host-side poll/delivery bridge or exact executable host job contract is needed; never assume HTTP 200 means user read. Preserve idempotency and uncertain-send reconciliation.
5. Integrate OpenGym via optional real MCP adapter with configured private endpoint/token. Use official MCP client SDK transport; allow read/search/preview initially, writes behind separate permission. No automatic deployment of unneeded OpenGym. No licensed media extraction. Add synthetic/mocked adapter tests and exact installation guidance.
6. Deployment: provide simple supervised run and Docker/reverse-proxy assets, stable HTTPS requirement, backup/restart process, no secret env in public files. No arbitrary paid host provisioning. Clear host-capability fallback if Dot can't execute or attach tools; don't degrade silently to a conversation and declare success.
7. Nutrition reminders: select times/preferences, quiet hours, budget, suppress logged meals, preserve photo estimates, edits and unknowns. If meals skipped or reminders stopped, don't count as zero food. Explain gap between queue producer and real host scheduler/WhatsApp connector.
8. Team catalog/blueprint and old active docs must reflect MVP/companion. Add full what/why/how roadmap, requirements matrix, source-referenced decisions, host install contract and device acceptance checklist. No raw transcripts, private IDs, names or accounts in public docs.
9. Tests: full legacy suite + new unique service tests, HTTP integration, official MCP client process roundtrip, fresh bootstrap twice preserving secrets, task/packet/delivery path and synthetic E2E demonstrator. Cross-platform paths/tzdata. Package links/manifest/archives/build validation. Release docs not counted as actual device testing.
10. Update root VERSION/pyproject/release assets to 0.2.0, build script ROOT_FILES allowlist for new root artifacts, CI dependencies before tests; concise public-safe `.second-brain/entries/` task result. App will verify/review/integrate, publish GitHub commit/release and reread actual remote. No push from artifact worker.

## Research already checked from primary sources

Authoritative URLs and implementation findings are in `docs/mvp/research-input.md`. Use these as provided evidence; distinguish code main vs installed iOS app version. No unrelated product named Dot may be assumed to be this participant's assistant. Research context can be requested from the app through contextRequests if genuinely missing.

## Acceptance for completion

One URL leads a tool-capable host into INSTALL without extra user prompt. Fresh private bootstrap works twice without data/credential loss. Synthetic HAE payload arrives over actual HTTP, is durably readable through authenticated host tools across restart, duplicate doesn't double-count, corrected value stays linked, scopes/pause/delete enforced. Roles have complete contracts and bounded task lifecycle. Prepared Persian section is deliverable through leased outbox with actual host-receipt field. Meal reporting/quiet reminders tested. OpenGym integration has honest ready/not-configured states. iPhone/HAE/host/channel gaps remain prominently unverified until actual receipts exist. Deliver code/docs/tests/install artifacts together, not a claim of device operation.
