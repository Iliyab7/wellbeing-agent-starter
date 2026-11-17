# Wellbeing Agent Starter

**Executing assistant: follow [INSTALL.md](INSTALL.md) immediately when this repository URL is shared for setup. Install or resume with actual tools; no additional launch prompt is required. ChatGPT Dot should use [its Work/Codex executor route](adapters/chatgpt-dot.md).**

The implemented 0.2.0 MVP keeps the participant's host as Chief of Staff, outside four wellbeing responsibilities: Manager, Analyst, Coach and Emotional Companion. Activate only relevant roles. Native workers require actual creation receipts; otherwise disclose host-executed virtual roles.

The implemented Python service provides private transactional SQLite memory, authenticated Health Auto Export intake, corrections/deduplication, scoped tools, bounded tasks, meal entries, pairing links and a leased delivery queue. The host supplies reasoning, media understanding and actual channel operations. Sheets/Notion mirrors require a separately verified adapter. OpenGym is optional and configured for reviewed reads/search/previews; licensed media forwarding is excluded.

ChatGPT web does not import local Codex MCP configuration or turn this service's OpenAPI specification into tools automatically. The current route is Dot delegating to a capable executor using private Python/REST or supported local MCP stdio. An authenticated remote MCP/OAuth plugin is future work. The root plugin manifest packages instructions; it is not a registered live integration.

Local code, transport, catalog compatibility, meal precision and reminder correction are verified by coordinator-reported executions. Release preflight passed build, 127-file validation, deterministic rebuild and extracted archive validation; [QA](qa/mvp-verification.json) tracks results, skips and the final metadata recheck. Real iPhone, Dot account, channel/scheduler, public HTTPS, Docker, OpenGym-server and backup/restore acceptance remain pending. Cloud-memory mirror and remote MCP/OAuth adapters remain unimplemented.

Python 3.11+ preserves the standard-library reference route:

```sh
python scripts/demo.py
python -m wellbeing --help
python -m unittest discover -s tests -v
```

HTTP/MCP checks require the optional pinned dependencies in `requirements-mvp.txt`; missing dependencies may skip integration tests. Install through the bootstrap in [INSTALL.md](INSTALL.md). Use the complete checkout, including roles and skills.

[Entry](START-HERE.md) · [Host behavior](CHAT-STARTER.md) · [Runtime](docs/runtime.md)

This is nonclinical assistance. Participant goals, recipients, retention and contact choices govern operation. Keep personal records and credentials outside this public repository.
