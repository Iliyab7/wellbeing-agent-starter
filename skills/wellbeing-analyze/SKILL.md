---
name: wellbeing-analyze
description: Answer nonmedical questions about authorized wellbeing observations and trends. Check provenance, units, missingness and comparability, distinguish observations from hypotheses and confirmed facts, and correct dependent findings when evidence changes.
---

# Build reliable, limited understanding

Start from the specific question and permitted purpose. Inspect only relevant authorized
sources. Preserve source ID, metric definition, unit, observation date/time, timezone,
measurement/self-report/planned-event status and quality. Report blocked access separately
from absent data, incomplete data and no observed change.

Check duplicates and conflicting observations. Do not sum overlapping wearable readings,
merge incompatible scoring scales or silently normalize unknown units. Missing is unknown,
not zero. Use comparable windows and enough coverage for the actual question; state the
coverage and limits. A one-value difference is not automatically a meaningful trend.
Population health cutoffs are not automatic personal action thresholds.

Use a personal baseline only when the data and source definition support it. A changed
device or recording method can explain an apparent change. Calendar plans do not prove
execution. Self-report is useful evidence with its own nature, not automatically inferior
or identical to a sensor. Do not imply that a named platform always exposes every metric.

Separate:

1. Observation: directly recorded/reported evidence with its provenance.
2. Hypothesis: a possible explanation, including alternatives and contrary evidence.
3. Confirmed information: what relevant reliable evidence actually establishes.

Repeated claims from multiple roles are not independent confirmation. Correlation is not
causality. A hypothesis may justify a targeted inquiry, not a dependent plan change. Ask
Manager for the missing context only when its value justifies further work or attention.

Return the useful answer, why it matters to the chosen goal, uncertainty, source references,
and a narrow next question only if needed. A sparse-data limitation is a valid outcome.
Do not produce a clinical diagnosis, treatment/medication advice, or automatic training/
diet changes. Use the host's appropriate human-care pathway for concerning content.

When corrected, mark the prior finding superseded and notify Manager which dependent
proposals should be reviewed. Stop use of a revoked source and honor the agreed treatment
of stored/derived data. Keep only authorized private records; never publish personal data.

Read [quality cases](references/quality.md) before handling ambiguous comparisons.

## Shared-memory use and registration

Read scoped authorized evidence from the active memory; record source-linked findings,
trends, uncertainty, checks, work events and reports under Manager's current contract.
Keep raw evidence separate, mark superseded findings and tell Manager which downstream
plans depend on corrected evidence. Claim reads/analysis completion only with the actual
evidence available. Do not fetch the whole shared dossier by default.

Record your own scoped work and exchanges with actor/time/status and stable links.
Use the [shared-memory contract](../../docs/shared-memory/README.md) when designing,
reading, writing or reviewing memory. Apply it within this skill's existing mission;
this module creates neither cloud infrastructure nor independent agents.
