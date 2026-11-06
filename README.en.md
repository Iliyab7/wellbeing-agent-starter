# Wellbeing Agent Starter

A portable initial-test kit for a personal assistant acting as Chief of Staff. Dot (or another capable host) replaces the original ELHAM interface and coordinates a Wellbeing Manager, Analyst and Coach. Roles are responsibilities, not a compulsory pipeline. The participant chooses goals, data access, recipients, authority, retention and contact preferences.

## Start a personal pilot

Give your assistant this repository and ask it to follow [START-HERE.md](START-HERE.md). If it cannot retrieve GitHub files, attach [CHAT-STARTER.md](CHAT-STARTER.md). The host checks its actual capabilities first and uses clearly labelled virtual roles when real subagents are unavailable. No wearable or API key is required for a conversation-only start.

The portable instructions are not proof of native Dot/Grok integration, persistent memory, isolation or background scheduling. Every connector or external action requires a real capability and the participant's applicable permission. Personal data stays out of this public repository.

## Run the reference checks

With Python 3.11+ from the extracted repository:

```sh
python scripts/demo.py
python -m unittest discover -s tests -v
python scripts/validate_package.py
```

These checks use synthetic data and require no external service. See [runtime commands](docs/runtime.md), [developer handoff](docs/harvey-handoff.md), [architecture](docs/architecture.md), [acceptance tests](docs/acceptance-tests.md) and [verification evidence](qa/verification.json).

The [team blueprint](agents/team-blueprint.json) and [orchestration playbook](docs/orchestration-playbook-fa.md) specify role goals, skills, capability grants, task assignment, report collection, review, closure and cancellation. The host records real agent IDs and action receipts only when its tools actually create them.

This is a nonmedical pilot package, not a clinically validated service or a deployed multiagent backend. It preserves the difference between evidence and hypotheses, between a delivered suggestion and actual implementation, and between an observed change and a causal effect.
