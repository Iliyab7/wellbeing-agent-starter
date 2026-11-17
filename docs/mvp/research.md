# HAE source-to-wire correction — 2026-11-17

This focused supplement uses primary-source excerpts supplied to the bounded implementation worker. It supplements [research input](research-input.md); it does not claim a new browser inspection, test execution or real-device verification.

| Official format | Wire array and relevant semantics |
|---|---|
| [Health metrics](https://help.healthyapps.dev/en/health-auto-export/export-format/health-metrics/) | `metrics`: name, units and sample data; preserve metric-specific observations. |
| [Workouts](https://help.healthyapps.dev/en/health-auto-export/export-format/workouts/) | `workouts`: source ID where available, start/end and duration. |
| [Symptoms](https://help.healthyapps.dev/en/health-auto-export/export-format/symptoms/) | `symptoms`: start/end, name, severity, cycleStart, userEntered and source. |
| [Cycle tracking](https://help.healthyapps.dev/en/health-auto-export/export-format/cycle-tracking/) | `cycleTracking`: start/end, name, value and isCycleStart. |
| [ECG](https://help.healthyapps.dev/en/health-auto-export/export-format/ecg/) | `ecg`: start/end, classification, averageHeartRate, voltageMeasurements, samplingFrequency and source. Nested voltage dates do not substitute for a missing event start. |
| [Medications](https://help.healthyapps.dev/en/health-auto-export/export-format/medications/) | `medications`: displayText, nickname, start/end, scheduledDate, status, isArchived, dosage, scheduledDosage, units and codings. The supplied format does not guarantee name, source or an ID. |
| [State of Mind](https://help.healthyapps.dev/en/health-auto-export/export-format/state-of-mind/) | `stateOfMind`: ID, start/end, kind, labels, associations, valence and valenceClassification; recorded self-report. |
| [Heart-rate notifications](https://help.healthyapps.dev/en/health-auto-export/export-format/heart-rate-notifications/) | **`heartRateNotifications`**, plural: heartNotification, start/end, threshold, source object and heartRateData. The [deep-link datatype](https://help.healthyapps.dev/en/health-auto-export/automations/deep-link/) remains **`heartRateNotification`**, singular. |

## Implementation decisions

`wellbeing/hae.py` normalizes the documented plural notification array into the existing singular internal category. Existing configuration, role scopes, record queries and deep links keep their singular spelling. Both upload spellings enter the same permission check and identity namespace. When both appear, identical observations deduplicate; conflicting versions of one observation reject the entire transaction. Unknown category keys, even alongside recognized arrays, raise an error. The accepted wrapper is `data`; bare category objects remain compatible. No additional envelope metadata is allowlisted without documented evidence.

An actual `id` or `uuid` retains precedence. Otherwise dated records keep the existing time/source/name fallback, extended for medications by displayText, nickname and codings, and for notifications by heartNotification. Dosage, scheduledDosage, status, isArchived, threshold and nested measured values remain outside these discriminators. Corrections to those values update the logical record and preserve its prior payload as a revision. This identity rule is an engineering fallback, not an exporter guarantee.

HAE example timestamps contain a space before an explicit numeric offset. Parsing removes that space and normalizes to UTC. Missing, malformed or timezone-free dates remain unknown; receipt time and nested measurement epochs are not guessed event times.

## Limits and verification boundary

Without stable exporter IDs, changes to event time, source or identity descriptors cannot automatically reconcile previous records. Two indistinguishable events with the same fallback identity cannot be separated reliably; conflicting payloads in one upload fail atomically. Untimed records use content identity, so changed content without a source ID cannot automatically be recognized as a correction. No retrospective rekeying or merging of existing SQLite records is performed. Previously stored medication/notification fallback IDs may coexist with records ingested under the corrected rule; any reconciliation needs an explicit scoped review. No data is silently migrated or deleted.

`tests/test_hae_wire.py` contains literal synthetic adaptations of all eight supplied primary formats, rather than generating wire names from runtime constants. Dates and nested epochs are refreshed together. Proposed checks cover plural HTTP ingestion through TestClient, replay, alias permissions/conflicts, simultaneous medications and notification types, numeric revisions, restart, concurrent alias replays, unknown categories and missing timestamps. These checks have **not been executed by the artifact worker**. TestClient exercises the HTTP application in process; it is not TCP, HTTPS, iPhone or background-delivery evidence. The reported earlier 92-test/TCP baseline predates this correction and does not verify it.
