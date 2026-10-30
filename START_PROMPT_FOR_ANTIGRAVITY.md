# Start Prompt for Antigravity CLI

Paste the following instruction into Antigravity from the root of the Krishi Mitra repository. Keep this document set available to the agent.

---

You are the lead implementation engineer for the Krishi Mitra AI backend. Read every Markdown file in `krishi-mitra-developer-pack/` before coding. Treat `README.md` and `00_EXECUTION_ORDER.md` as the entry point and follow the document precedence exactly.

First inspect the repository, current git status, existing architecture, branches, tests and uncommitted work. Do not overwrite existing user changes. Then map the repository to the approved specification and report conflicts.

Implement only M0.1 and M0.2 from `15_IMPLEMENTATION_PLAN.md` in this first execution: (1) a runnable FastAPI backend foundation with configuration, health endpoints, PostgreSQL connectivity/migrations, safe structured logging, Docker/local setup and tests; (2) a local Ollama adapter for configurable Qwen3 4B with schema-constrained intent/slot extraction, Pydantic validation, timeouts, bounded retry and Kannada fixtures. Keep model inference outside the FastAPI event loop.

Do not begin the speech, dialogue, scheme, authentication or scaling milestones until M0.1/M0.2 are runnable and their acceptance tests pass, unless a prerequisite issue is discovered. Do not create mock “complete” modules that merely return hard-coded success.

Non-negotiable constraints: no paid external AI APIs; no admin role/dashboard/routes; no LLM eligibility decision; no invented PM-KISAN/PMFBY rule criteria; synthetic schemes must be explicitly marked demo-only; no raw audio persistence by default; no farmer data or secrets in logs or git; no unsupported 1,000-user capacity claims.

At completion, report status, files changed, API/database changes, exact commands run, exact test results, manual verification, known limitations and prerequisites for M1. Do not commit or push unless explicitly instructed.

---
