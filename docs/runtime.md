# Runtime contracts — MVP SQLite and legacy JSON

Two independent runtimes coexist. **MVP 0.2 uses private SQLite** and optional pinned dependencies; **`python -m wellbeing` retains the standard-library JSON reference CLI**. Their homes, policies, schemas and task states differ. There is no implicit migration, cloud synchronization or interchangeable input format.

## MVP installation and operation

The executing host follows [INSTALL](../INSTALL.md) and [the ChatGPT Dot executor route](../adapters/chatgpt-dot.md). Example commands, with an actual authorized private directory outside the checkout:

```text
python scripts/bootstrap.py --home PRIVATE_DIR --install
python scripts/doctor.py --home PRIVATE_DIR
```

Supply `--public-url` only with the approved stable HTTPS base URL. Bootstrap generates private configuration/credentials and refuses silent recovery when an existing store loses credentials. Repetition preserves credentials; phone pairing deliberately rotates intake credentials. Import private tool configuration only into a host that actually supports it. Never paste secrets into public files or shell arguments.

Default MVP home is `~/.wellbeing-mvp`, selected by `--home` where supported or `WELLBEING_MVP_HOME`. Use the installed private runtime interpreter. Run `scripts/run_server.py` with private environment configuration for REST; it defaults to loopback port 8787. `scripts/run_mcp.py` exposes official MCP SDK stdio using `WELLBEING_ROLE_TOKEN`, private home and optional `WELLBEING_PUBLIC_URL`. Stdout belongs to MCP. A host must actually attach/use these tools; ChatGPT web does not import local MCP configuration or automatically turn OpenAPI into tools.

`requirements-mvp.txt` pins the optional runtime. `doctor` inspects an existing store and dependency versions; optional `--health-url` probes `/healthz`. A healthy local service proves neither public reachability nor phone/channel operation. Docker/compose assets exist but live Docker acceptance remains unverified.

## Store, authority and intake

SQLite transactions serialize writes; schema startup checks reject unsupported newer versions. Role credentials are hashed in the database, while private host configuration contains usable credentials. The store is not encrypted at rest. Protect OS permissions, Windows ACLs, disk/volume and backups separately.

Provisioning starts with no Health categories shared and reminders disabled. Technical retention/timezone/reminder defaults are not participant decisions; resolve valid purpose, recipients/providers, retention and attention before personal use. `configure` replaces top-level settings, merges reminder fields and validates category scopes. It is host/Manager-authorized technically; it does not itself establish consent.

HAE intake accepts eight categories with role-scoped reads. Official `heartRateNotifications` maps to internal `heartRateNotification`; both spellings use the same permission and identity namespace. Unknown categories or malformed/conflicting batches fail transactionally. Source `id`/`uuid` is preferred; otherwise identity is best effort. Dated medication/notification discriminators reduce collisions. Changing time/source/descriptors can create a different identity; untimed changed content without an ID cannot reliably become a correction. No retrospective rekeying occurs. See [wire research](mvp/research.md).

Identical replay is unchanged; recognized corrections retain prior payload revisions. Event time and receipt time are separate; missing/naive/malformed event time stays unknown. Missing is not zero. Bounded history must fit selected retention; expired observations are not retained. Pairing creates expiring single-use private links, selected categories/recipients/retention and generated HAE links. This is configuration, not a phone-connection receipt. iOS grants, app review/purchase and enabling exports are human device steps; background cadence is not guaranteed.

Scope changes, corrections and retention can conservatively delete derived context/packets/plans/findings and tasks, and cancel pending output. Category reduction removes disallowed records/revisions. Ordinary entry reads exclude `emotion`/`support` for host/Manager, but tasks/reports and shared host context are separate exposure paths. Entry access is not a task-level sandbox or consent engine. Free text must be minimized by the executor.

Retention is opportunistic during relevant service operations and tick; an inactive process guarantees no deadline cleanup. Whole-store deletion logically removes runtime records, revokes credentials and disables service. It does not erase backups, SQLite file remnants, chats, exports or external copies.

## Host tools and bounded work

REST operations under `/v1` and corresponding `wellbeing_*` MCP tools expose status, records, entries, tasks, packet, configuration, pairing, delivery and optional OpenGym. REST additionally supplies the explicit-confirmation privacy deletion operation. Keep role credentials separate; specialists do not receive the host credential.

Task `create` accepts `id`, `role`, `objective`, nonempty `acceptance` and optional `evidence_ids`. Evidence must be shared with sender and assigned role. Creation returns `prepared`, `dispatched: false`. An identical contract ID reuses existing work; changed work under that ID fails.

| Operation/state | Meaning |
|---|---|
| `claim` → `running` | Assigned role gets selected evidence and a 15-minute lease/token; no worker is spawned |
| `report` → `report_received` | Matching role/current lease supplies `result` and `uncertainty`; not verified |
| `review` accept → `verified` | Host/Manager of a different responsibility accepts with a reason |
| `review` revise → `prepared` | Reclaim and perform targeted revision |
| `close` → `closed` | Internal accepted work finished; delivery is not implied |

`tasks` lists scoped IDs/states; `get` exposes contract/report/review to assigned role or host/Manager. Expired running leases can be reclaimed, so host side effects must not be blindly repeated. There is no general task cancel/blocked/expired operation in this MVP API; pause cancels tasks and scope/invalidation may delete them. Manager tasks require host review. Native worker lifecycle and cancellation require actual host operations separately.

Role entries require `id`, `kind`, object `payload`; existing identity is bound to original role/kind. Meals require meal type and provenance, with either timezone-bearing `occurred_at` (optional `time_precision: exact`), or `time_precision: day` and local `occurred_date` (`YYYY-MM-DD`) without `occurred_at`, or `time_precision: unknown` without either occurrence field. Day/unknown records preserve declared `timezone` or the current participant timezone; no clock or occurrence date is inferred from receipt time. Date-only records retain their declared local date. Exact timestamps use the current participant timezone for reminder matching. Only a matching dated meal/slot suppresses queued reminders; unknown drafts and previous-day meals do not suppress today's reminder. Resolve explicit “today” using actual conversation date/timezone or known reminder association; ask only consequential ambiguity, not an exact hour by default. Photo estimates require `nutrient_certainty: estimate`; grams/calories are optional and skipped/declined entries cannot carry nutrients. Actual host vision/transcription is required. Same-ID/same-role corrections preserve one current entry. Past sends are not recalled.

## Queue production, delivery and host jobs

The API ticker attempts reminder production every 60 seconds while running. Participant-selected meal times, quiet hours, grace and budget govern production. It sends no WhatsApp messages. A stored packet with `text` queues a wellbeing section; `packet()` retrieves prepared material and scoped observations, not an automatically reasoned newsletter.

Host-only delivery claim runs tick and leases pending output for five minutes, returning claim token and idempotency key. Use the actual authorized channel within current scope and lease. Acknowledge with real `receipt_ref`, ID and token only after observed send success. Expired leases become `uncertain` when processed; they are not automatically resent. Reconcile through actual channel lookup: `delivered`, confirmed `not_sent` (eligible again, subject to expiry), or `unknown` (remains uncertain). A host-supplied receipt is not independently authenticated proof or evidence of reading/acting. Recheck cancellation before sends; separate service and channel operations are not atomic.

`scripts/host_tick.py collect --home PRIVATE_DIR --output FRESH_PRIVATE_JOB` collects host deliveries/task metadata or claims one specialist task using its role credential. The host loads role instructions, performs actual reasoning/channel calls and writes a separate private result file. `apply --home PRIVATE_DIR --results PRIVATE_RESULTS` persists reports, actual delivery receipts or reconciliations. These files contain sensitive data/tokens; retain unresolved jobs for reconciliation and remove processed files under policy. The script registers no recurring job, creates no agents and supplies no channel/model API. Manager review/closure stays explicit.

Optional OpenGym needs enablement plus private endpoint/token environment and reviewed advertised read/search/preview mapping. `status` distinguishes configuration from successful initialization/tool listing. Calls return external evidence, not authority; no primary-memory write, external workout write or restricted-media forwarding is implied.

## Legacy standard-library reference

Default home is `~/.wellbeing-starter`, selected by `--home PATH` before the subcommand or `WELLBEING_HOME`. State is plaintext JSON with atomic replacement and a single-writer lock, distinct from SQLite. The invoking host/operator sees output; role packet labels are not isolation from it.

```text
python -m wellbeing --help
python scripts/demo.py
python -m wellbeing --home PRIVATE_REFERENCE_DIR status
```

Existing commands remain: `init`, `configure`, `import`, `source-status`, `analyze`, `team`, `packet`, `verify-packet`, `task`, `check-in`, `plan`, `review`, `correct`, `delete-record`, `set-goal`, `pause`, `resume`, `revoke`, `export`, `delete`, `status`. Use command help and `schemas/` for exact inputs; conversational templates are not CLI schemas. Consent confirmation flags attest actual participant agreement, not sample-command authority.

The legacy path makes no network calls. `team --mode inline|native` prepares manifests only; packets are prepared, not sent. Its task ledger uses explicit dispatch/reconciliation and review states separate from MVP leases. Its policy validates purpose, expiry, sources/units, recipients, journal, authority and attention; it is not MVP configuration. Corrections/revocation invalidate dependent reuse; retention occurs on invocation and persists after successful commands. Output is JSON with escaped Unicode; expected errors return exit code 2. Existing zero-dependency commands/tests remain usable without HTTP/MCP packages; optional tests must report skips.

## Verification boundary

Release checks: `python -m unittest discover -s tests -v`, `python scripts/demo.py`, `python scripts/mvp_smoke.py`, then `python scripts/build_release.py` and `python scripts/validate_package.py`. Full MVP checks require optional dependencies. Record actual revision/results and distinguish received historical evidence from current execution.

Coordinator baseline at 2026-11-17T13:17:39Z: 104 tests, OK with one skip; loopback TCP/restart smoke and legacy demo passed. Private installation/repeat credential preservation and local health were also observed separately. Real phone, Dot, WhatsApp, public HTTPS, Docker and live OpenGym acceptance remain pending. Detailed operational ownership and remaining gates are in [handoff](harvey-handoff.md).
