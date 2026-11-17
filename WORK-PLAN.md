# MVP delivery plan — 2026-11-17

## Outcome
Give a capable host only this repository URL. It reads the root entry, provisions a private runtime, discovers its real tools, connects an iPhone intake route, prepares the wellbeing team, and returns a receipt-based setup status. Human steps are limited to device permissions, payment choices, account authentication and material preferences. A repository link cannot grant missing platform capabilities.

## Work packages and acceptance

1. Inspect baseline and primary documentation; record choices and alternatives in `docs/mvp/research.md`.
2. Build resumable bootstrap and a machine-readable host contract; do not treat conversation-only fallback as installed MVP.
3. Build authenticated Health Auto Export intake, generic category coverage, durable private storage, revisions, deduplication, freshness and revocation.
4. Generate per-participant iPhone setup links on a protected pairing page; no long-lived secret in chat/GitHub links.
5. Expose REST/OpenAPI and official SDK MCP tools for host assistants. Preserve the existing reference CLI.
6. Prepare Manager, Analyst and Coach plus explicitly requested Emotional Wellbeing Companion. Provide dispatch, reports and acceptance records; use host inference rather than requiring another paid model.
7. Implement meal/self-report intake, timezone-aware meal reminders, quiet hours, suppression after logging and delivery receipts. Host handles authorized photo/voice understanding; no fabricated transcription or nutrient certainty.
8. Integrate OpenGym as an optional, permission-scoped MCP tool source. No redistribution of licensed animations or copying its implementation.
9. Test HTTP, restart, retries, concurrent writes, correction, revoked authority, tasks, pairing, reminders, host installation and malicious inputs with synthetic data.
10. Publish a checked GitHub package/release, reread remote artifacts, and hand off actual iPhone/host acceptance steps. Mark real-device and Dot checks unverified until observed.

## Delivery gates

- Package/local gate: automated tests, fresh installation, synthetic phone → HTTP → memory → host tools → packet → outbox → receipt flow.
- Reachability gate: stable public HTTPS URL on participant-approved always-on host; localhost alone is not iPhone connectivity.
- Device gate: iPhone permissions + first real upload + delayed/background catch-up measured.
- Host gate: Dot/other host reads tools, runs relevant roles and registers a real recurring trigger or acknowledges its lack.
- User gate: reports, reminders and privacy preferences accepted; no silence-as-approval.

## Primary architecture decision

Extend the established Python stack. Host supplies inference/vision/transcription and existing WhatsApp identity. Python service supplies deterministic ingestion, tools and durable workflow. No new eve/Vercel model dependency: this is an existing non-eve runtime and a host-installable team, not a replacement chief-of-staff app. SQLite is the private transactional primary store in MVP; Sheets/Notion can be explicitly configured mirrors/host memory, never implied working connectors.
