# Working on Wellbeing Agent Starter

This repository is the public, initial-test implementation package. Read README.md, START-HERE.md, docs/architecture.md, docs/source-analysis.md and docs/harvey-handoff.md before changing behavior. Runtime instructions for a participant's assistant live in CHAT-STARTER.md and agents/, not in this contributor file.

Preserve the responsibility-based design: the host assistant (Dot or another capable host) is Chief of Staff; the Wellbeing team consists of Manager, Analyst and Coach. Do not turn those roles into a mandatory pipeline or add permanent agents for every domain. Native subagents are used only when the host actually supports them; otherwise label the roles as virtual within one assistant. Never claim persistent agents, connectors, notification schedules or clinical validity without observable evidence.

Goals, data scope, retention, sharing recipients, authority and attention policy are participant decisions. Existing authorized context comes before repeated questions. Reversible internal organization can proceed inside the agreed scope; new sources, new recipients and external side effects require the applicable authority. No generic fixed health thresholds or mandatory daily reporting. Separate observation, hypothesis and participant confirmation. Separate delivery, implementation and observed outcome.

Use synthetic fixtures for tests. Never commit personal health data, real transcripts, credentials, account exports or participant state. Local state must default outside the repository. Keep the original private definition repository unchanged; source summaries here are public-safe adaptations, not copies of the raw history. Public access is not permission to publish participants' data.

Run `python -m unittest discover -s tests -v`, `python scripts/demo.py`, rebuild with `python scripts/build_release.py`, and run `python scripts/validate_package.py` for a release. Report reference-runtime checks separately from real-host pilot testing. Do not mark manual pilot cases passed without a transcript/result and participant agreement to retain that evidence.

For substantive changes record a concise public-safe task result in `.second-brain/entries/`, including decisions, actual checks, blockers and next actions. This is project evidence, not a promise of automatic synchronization with any private memory system.
