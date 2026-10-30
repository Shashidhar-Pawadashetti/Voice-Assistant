# 17 — Antigravity CLI Developer Instructions

You are the implementation engineer for **Krishi Mitra AI backend**. Treat the other documents in this folder as the approved specification. Your task is to build the working system, not merely produce another plan.

## 1. First action: inspect, do not overwrite

- Inspect the repository root, git status, branches, existing code, lock files, tests, Docker config and `.env` presence.
- Preserve all existing changes.
- If the current repository includes frontend code, do not rewrite it. Build the AI backend in a clearly separated directory or use the project's existing backend layout.
- Report the discovered structure and any conflicts with this specification.

## 2. Technical decisions you must follow

- Python 3.11+ / FastAPI / Pydantic v2.
- PostgreSQL as persistent source of truth.
- Qwen3 4B via local Ollama as the first LLM candidate; make it configurable and verify Kannada quality.
- AI4Bharat IndicConformer Kannada as primary ASR candidate.
- Faster-Whisper only as an evaluated candidate; do not assume it is a better fallback.
- AI4Bharat Indic-TTS Kannada as TTS candidate; verify exact checkpoint terms/runtime before bundling.
- Deterministic dialogue state machine.
- Deterministic, versioned scheme rule engine with TRUE/FALSE/UNKNOWN.
- No LLM eligibility decisions.
- No admin role, admin dashboard or public scheme mutation routes.
- Raw farmer input audio is transient and not persisted by default.
- Open-source/local-first. Do not add paid external AI APIs.

## 3. Milestone execution

Implement the milestones in `15_IMPLEMENTATION_PLAN.md` in order. Start with M0.1 and M0.2. Do not attempt M1–M7 before the foundation is testable unless the project owner explicitly asks for a different sequence.

For every milestone:

1. make a short task plan from acceptance criteria;
2. implement production-shaped code, not toy examples, within scope;
3. write tests before marking a task complete;
4. run formatter, lint/type checks and tests;
5. update docs, `.env.example`, migrations and OpenAPI as appropriate;
6. report exact changed files and test command output;
7. identify unfinished work honestly.

## 4. Code quality requirements

- type annotations on public functions;
- Pydantic request/response schemas;
- dependency injection for DB/model clients;
- timeouts around all network/model calls;
- bounded retries with backoff and jitter;
- structured logs with secret/PII redaction;
- no blocking GPU/model inference in the async event loop;
- no shell interpolation when calling FFmpeg;
- transaction boundaries and optimistic conversation versioning;
- migration scripts for DB schema;
- tests for all failure paths and ownership checks;
- no hard-coded secrets, URLs, model IDs or retention values outside configuration where they may change.

## 5. LLM safety requirements

- Model output is untrusted.
- Use constrained JSON output where supported and validate against Pydantic.
- Reject additional/unexpected fields or use strict schemas.
- Do not let model output set verification status, role, farmer ID, rule version or eligibility outcome.
- Do not allow the model to call the DB, filesystem, shell or public internet.
- Treat farmer transcripts as data, never as instructions that can override system policy.
- When extraction is invalid or ambiguous, preserve prior valid state and ask a clarification question.

## 6. Scheme-data safety requirements

- Load the five seed records from `08_SCHEME_CATALOG_SEED.md`.
- PM-KISAN and PMFBY must remain `INCOMPLETE`/`RULES_NOT_VERIFIED` until exact current official criteria are sourced, encoded and tested.
- Do not create invented thresholds/benefit amounts/documents/deadlines for the real schemes.
- All demo schemes must carry `SYNTHETIC_DEMO` and `demo_only=true` through database, API and response generation.
- No scheme CRUD endpoint or admin page.

## 7. Privacy/security requirements

- Authenticate before accessing a conversation.
- Scope all farmer-owned data by farmer ID from the auth context.
- Never trust farmer ID sent by frontend.
- Argon2id password hashing.
- Refresh token rotation and revocation.
- Protect temporary audio and delete it on all exit paths.
- No raw audio/transcript/prompt/secret in logs.
- Deletion must include data, cache, temporary media and pending jobs.
- Do not collect Aadhaar/bank/voiceprint data.

## 8. Integration requirements for frontend team

- Expose versioned REST endpoints documented in `09_API_CONTRACT.md`.
- Publish FastAPI OpenAPI spec.
- Provide CORS configuration via environment variable for the known frontend origin.
- Keep model ports internal; frontend calls only backend.
- Provide text fallback and job polling.
- Use request IDs and idempotency keys.
- Keep audio response URL private and authorized.

## 9. Do not do these things

- Do not replace the state machine with an unrestricted chatbot/agent.
- Do not introduce LangChain/LangGraph/vector DB unless a documented requirement proves the need.
- Do not deploy model weights or farmer data to free public notebooks as a shortcut.
- Do not create an admin role “for convenience”.
- Do not claim scheme eligibility based on a prompt.
- Do not mark a model “accurate in Kannada” without evaluation evidence.
- Do not claim 1,000 simultaneous AI jobs without load testing and a stated hardware profile.
- Do not commit model weights or `.env`.

## 10. Final report format

At the end of each milestone return:

```text
Milestone:
Status: COMPLETE / PARTIAL / BLOCKED
Summary:
Files changed:
Database/API changes:
Tests executed:
Test results:
Manual verification:
Known limitations:
Security/privacy notes:
Next milestone prerequisites:
```

Do not say “complete” if tests were not run or any acceptance criterion is unmet.
