# Primary-source research input — checked 2026-11-17

These notes are research evidence for implementation, not live device acceptance. Paraphrased facts; do not copy whole source documents into this public package.

## Health intake and setup

- [HAE deep links](https://help.healthyapps.dev/en/health-auto-export/automations/deep-link/): `com.HealthExport://automation?...` creates REST API automations. `url` required. Order datatype before data options and format before aggregation options. `headers` consists of comma-separated alternating keys and values, e.g. `Authorization,Bearer TOKEN`, NOT colon syntax. URL encode with percent encoding. `syncinterval` is minutes/hours/days/weeks; `syncquantity` is a positive count. `notifyonupdate` and `notifywhenrun` booleans. Exports default disabled pending user review. `period=none` is default today+yesterday; `lastsync` and `previous7days` available. Workouts use `includeroutes`, `includeworkoutmetadata`, `workoutsmetadatainterval` minutes/seconds. Default route inclusion is true, so explicitly disable in our setup. All-metrics selection is omission of `metrics`; participant must explicitly choose it.
- [REST API](https://help.healthyapps.dev/en/health-auto-export/automations/rest-api/): HTTP POST to configured URL, custom headers, JSON v2 recommended, one data type per automation, batching for large data, manual upload for bounded history/catch-up. Device must be unlocked to read Health; background frequency not guaranteed.
- [Automations](https://help.healthyapps.dev/en/health-auto-export/automations/): background execution controlled by iOS and Background App Refresh; low power/inactivity can delay. Shortcuts/widget/manual are recovery triggers. Logs distinguish preparation from upload. Source selection and shorter/coarser exports improve performance. Automation config backup is not a backup of Health data.
- [Data catalog](https://help.healthyapps.dev/en/health-auto-export/getting-started/supported-data/): Health metrics (150+), workouts, symptoms, ECG, HR notifications, State of Mind, cycle tracking, medications. Availability depends on recorded data, device, OS, region and permissions. State of Mind iOS18+, medication exports iOS26+. No raw private data was fetched.
- [Metric JSON](https://help.healthyapps.dev/en/health-auto-export/export-format/health-metrics/): metrics array with name/units/data; source optional, timestamp with timezone, heart rate min/avg/max, sleep summary or individual phases, HRV SDNN. Keep metric-specific semantics; do not sum rerun totals or turn missing into zero.
- [Workout JSON](https://help.healthyapps.dev/en/health-auto-export/export-format/workouts/): workouts array; id, name, start/end, duration seconds; optional source, energy, distance, HR time series, routes, sport-specific fields. Match self-report to actual session; workout does not identify weights/reps.
- [State of Mind JSON](https://help.healthyapps.dev/en/health-auto-export/export-format/state-of-mind/): recorded self-report entries, not automatic psychological diagnosis. ID, timestamps, kind, labels, associations, valence.
- [Pricing](https://help.healthyapps.dev/en/health-auto-export/purchases/pricing/): checked US listed Basic $2.99 once, Premium $6.99/year or $24.99 lifetime, 7-day all-features trial. Automatic REST exports require Premium; check actual local purchase screen. No purchase authorized by these notes.
- [App Store](https://apps.apple.com/us/app/health-auto-export-json-csv/id1115567069): actual iPhone app, exports user-selected Apple Health information. Installation is on phone, not watch; no assumption of every gadget measuring every metric.

## Tools and host contracts

- [MCP transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports): stdio uses newline-delimited JSON-RPC only on stdout; Streamable HTTP distinct. Use official SDK, not an invented JSON endpoint labelled MCP.
- [MCP Python v1](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x): implementation pins MCP 1.30.0; latest 2.x changes API. Test actual SDK client initialization/list_tools/call_tool.
- [OpenGym MCP](https://github.com/DuarteSantos8/openGym/blob/main/mcp/README.md): self-hosted training bridge with history, routines, previews and workout logging; needs actual configuration/authority. MCP is not a WhatsApp connector. External write does not prove primary-memory write.
- [OpenGym catalogue](https://github.com/DuarteSantos8/openGym/blob/main/catalogue/README.md): text exercise catalog can assist selection. Scope/quality of Persian aliases still needs checking.
- [OpenGym media notice](https://github.com/DuarteSantos8/openGym/blob/main/catalogue/media/NOTICE.md): media licensed specifically for OpenGym; no independent extraction/forwarding assumed. Use native app/page links or separately licensed material. Do not copy implementation into our package.
- [OpenGym vitals](https://github.com/DuarteSantos8/openGym/blob/main/frontend/src/lib/vitals.js): selected sleep/steps/resting HR/HRV phone-local in checked source. Therefore installed OpenGym is not our full Health export bridge.

## Role evidence and limits

- [WHO Psychological First Aid](https://www.who.int/publications-detail-redirect/9789241548205): humane practical support, listening and linkage. Basis for limited supportive posture, not proof of AI therapy efficacy. No imitation of a famous psychologist as qualification.
- [NIDDK food portions](https://www.niddk.nih.gov/health-information/weight-management/just-enough-food-portions): a food diary distinguishes food/amount/time and estimated calories. A food photo is not measured grams/ingredients; preserve uncertainty and don't invent nutrition facts.

## Design alternatives considered

HAE REST is initial chosen candidate because it offers an existing iPhone app, documented export and setup links, and selected categories. Native Shortcuts is useful as a recovery/event trigger but requires device setup and doesn't remove Health access constraints. Gmail/Drive route can work with hosts lacking an API tool but needs actual connector tests and careful duplicate handling. A custom HealthKit app increases distribution/maintenance burden before validating this MVP. OpenGym remains optional exercise tooling. Existing Python stack and host inference are extended; a new model-specific platform was not substituted.
