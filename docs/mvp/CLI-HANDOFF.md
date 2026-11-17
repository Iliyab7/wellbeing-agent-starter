# Current implementation handoff — 0.2.0 candidate

## Delivery contract

The participant gives only this repository's root URL to **ChatGPT Dot**. The executing host follows [INSTALL](../../INSTALL.md), reuses an existing valid private installation and advances setup with actual tools. It asks only for missing participant decisions, device permissions, authentication, cost choices or a necessary connection. It does not ask the participant to select MCP versus API or copy another launch prompt.

ChatGPT Dot is CoS outside the wellbeing team: relationship, authority, coordination and attention remain with it. Manager owns organization, bounded work and recording duties; Analyst owns correctable understanding; Coach owns feasible chosen help; Companion owns bounded emotional support. Roles are activated as needed. Native workers require real creation/execution receipts; otherwise disclose virtual role perspectives. Team work returns ready packets/links.

## Current implementation boundary

The runtime supplied for integration includes private SQLite primary memory, authenticated selected HAE intake for eight categories, replay/corrections and revisions, scoped reads/entries, task/report/review, temporary pairing, generated HAE setup links and a leased delivery outbox. Meal reporting uses actual host text/vision/transcription capabilities; reminders are optional and retain quiet-hour, budget, suppression and delivery distinctions. OpenGym is optional configured tooling. The coordinator reported correcting its SDK client factory and adding a signature-bound regression.

Bootstrap/dependency installation, root setup entrypoints and runtime integration are implemented. [Catalog compatibility](../../tests/test_role_catalog.py), [meal precision and reminder correction](../../tests/test_meal_precision.py) are locally verified together. The eligibility-checked rearm fix preserves delivered, uncertain and prior-lease evidence; it does not blindly resend. Package and live acceptance remain separate gates.

The standard-library JSON CLI remains a separate reference contract. SQLite state is private and outside the repository; neither state format is implicitly migrated or synchronized. Manager-owned Sheets/Notion mirrors require their own authorized adapter, readback, correction and deletion. There is no verified cloud synchronization.

## Working ChatGPT route

Follow [the ChatGPT Dot adapter](../../adapters/chatgpt-dot.md) and [host contract](host-contract.md). Dot delegates a bounded task to an actual Work/Codex executor able to run private Python/service REST or supported local MCP stdio. Check capability, private persistence and service lifetime separately. A cloud computer or thread does not prove an always-on server or recurring trigger.

ChatGPT web does not read local Codex MCP configuration or automatically turn OpenAPI into tools. The portable [plugin metadata](../../plugin.json) packages instructions; it does not prove registered or published tools. Authenticated remote MCP/OAuth is a pending adapter. Follow-up implementation would need a remote MCP transport/server module, OAuth protected-resource and authorization-server integration, audience/PKCE/redirect validation, deployment configuration and negative authorization/transport tests. Select names and contracts before implementing; do not document these as existing runtime files. Sensitive public MCP must not use unauthenticated access.

Coordinator-provided official references: [Dot computers and apps](https://learn.chatgpt.com/docs/dots/computers-and-apps.md), [ChatGPT MCP](https://learn.chatgpt.com/docs/extend/mcp.md), [remote MCP server guide](https://developers.openai.com/api/docs/guides/custom-mcp-server.md), and [plugin authentication](https://developers.openai.com/plugins/build/auth.md). These describe platform mechanisms, not acceptance in this participant's account.

## Source-backed decisions

[Research input](research-input.md), [decision research](research.md), [Persian roadmap](ROADMAP-FA.md) and [requirements](requirements.json) distinguish official source statements, implementation choices and unverified behavior. HAE REST was selected as the initial phone route; no fabricated signed Apple Shortcut is supplied. Runtime pairing generates exact private links. Bounded history plus incremental/replayed input must retain source identity, correction, freshness and unknown states. All-data selection is optional and explicit.

Checked US HAE Premium pricing in the supplied research was a seven-day trial, $6.99/year or $24.99 lifetime. Check the actual local purchase screen; research is not purchase authority. OpenGym app/page links may be returned within scope; licensed media must not be independently extracted or forwarded.

Use useful ECC architecture/verification and V2 compact entry, progressive skills, bounded contracts and evidence-linked continuation selectively. The supplied V2 bundle is a laboratory proposal, not adopted policy. Existing code remains the authority for implemented behavior: do not infer CAS, event sourcing, automatic downstream deletion, global observers or new wellbeing roles from those references. Any required runtime addition needs an explicit source/test change.

## Observed evidence and current status

Actual bridge/app executions reported by the coordinator:

- **2026-11-17T13:57:19.662Z:** 124 tests in 9.225s, OK with one Windows symlink skip; loopback TCP HTTP/restart smoke, legacy demo and public structure/link/metadata validator passed.
- **2026-11-17T14:05:24.386Z:** after fixture-only portability changes, installed 124 tests in 8.652s passed with one skip; no-site `python -S` 124 tests in 6.394s passed with ten explained skips, and the no-site legacy demo passed. Runtime unchanged.
- **2026-11-17T14:08:12.5805643Z:** release preflight passed build, full manifest/hash/public validation for 127 files, identical archive SHA on second build and extracted archive validation for 127 files. Only final evidence/Markdown changed afterward; runtime/build scripts unchanged.

Catalog projection preserves legacy permissions; exact/day/unknown precision and the reminder rearm fix with nine regressions are locally verified. Earlier no-site timezone failures were corrected through explicit UTC generic/cross-participant fixtures; two actual default-Tehran bootstrap cases conditionally skip without IANA data, preserving installed coverage. [QA](../../qa/mvp-verification.json) records historical/current evidence and is authoritative for the final metadata recheck. Artifact workers executed no checks. Live acceptance remains pending.

## Final local verification

Install optional dependencies, then run from the composed repository root:

```bash
python -m pip install -r requirements-mvp.txt
python -m unittest discover -s tests -v
python scripts/demo.py
python scripts/mvp_smoke.py
python scripts/build_release.py --source-revision 0c0bfe0ee62d061d66feec76e6c4048d44973521
python scripts/validate_package.py
```

The explicit revision is the canonical source input sealed after equivalent tested bytes. Use the actual input code commit if source changes. The builder can discover checkout HEAD; an extracted archive may reuse its manifest's input revision or receive `--source-revision`. Manifest hashes identify packaged bytes; `source_revision` is input provenance, not a claim that tests ran against an already sealed commit or that a later evidence/manifest commit must equal it. Rebuilding unchanged input is deterministic.

[The optional helper](../../scripts/ci_mvp.py) checks installed dependency pins and runs the same checks, stopping at the first failing command. It does not install packages or turn skips into passes. Main CI includes dependency installation and TCP smoke across the existing matrix; remote execution is unverified. Local test/demo/smoke and release preflight results are recorded; QA tracks the final metadata recheck after evidence changes. Leave its artifact_sha256 null and provide the final archive digest externally in `dist/SHA256SUMS.txt` and the GitHub release asset. Standard-library reference checks remain usable with disclosed optional-dependency/IANA skips.

## Open live gates and next owner

Before claiming an installed live service, the authorized host/operator must establish approved stable HTTPS, private persistent storage, supervised restart and tested backup/restore. SQLite is not encrypted by this package; OS/disk permissions, backups and host/provider exposure require an explicit deployment decision. Follow [deployment](deployment.md).

Then use [the acceptance checklist](ACCEPTANCE-FA.md) with one real participant-approved phone: selected Health permissions, first upload/readback, history/replay/correction, delayed/background catch-up, pause/revocation/deletion and actual freshness. Verify ChatGPT Dot executor access, bounded task/report/review, native receipts or virtual disclosure, recurring trigger if selected and an actual channel delivery receipt. A queue item is not a WhatsApp send; sent is not read, adopted or executed. Uncertain sends require reconciliation before retry.

Real iPhone/HAE, Dot account execution, WhatsApp, public deployment, Docker, real OpenGym-server behavior and participant usefulness remain unverified. Emotional support is nonclinical; no diagnosis, treatment change or monitored crisis coverage is claimed. Retain live evidence only within participant agreement and outside the public repository.

Next owner: app applies the final evidence correction, rebuilds/revalidates the final archive and extracted contents, and mechanically records actual final_metadata_recheck receipts in QA. Authorized host/operator closes the separate deployment/device/host/channel/participant gates. Publishing, deployment and account access are outside this artifact worker's scope; no publication is claimed.
