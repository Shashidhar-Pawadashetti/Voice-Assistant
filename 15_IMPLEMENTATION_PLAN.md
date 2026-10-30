# 15 — Implementation Plan (M0–M7)

## Delivery approach

Implement one stable, testable vertical slice at a time. Each milestone must leave the repository runnable. Avoid building all modules as empty stubs. Branch strategy and commits should follow the team's Git conventions; the agent must not force-push or commit without authorization.

## M0 — Foundation

### M0.1 Backend project skeleton

Deliverables:
- Python project and dependency lock;
- FastAPI app with `/health/live` and `/health/ready`;
- configuration via Pydantic Settings;
- structured logging with redaction;
- Dockerfile and local Compose for API + PostgreSQL;
- `.env.example` and `.gitignore`;
- test/format/lint commands documented.

Acceptance:
- fresh clone can follow README and start service;
- tests pass;
- secret scan shows no committed secrets;
- readiness checks DB safely.

### M0.2 Local LLM adapter and structured extraction

Deliverables:
- Ollama client adapter;
- configurable `qwen3:4b` model;
- extraction Pydantic schema and JSON Schema;
- prompt that prohibits inference of missing facts and scheme decisions;
- timeout, one retry, parse/validation errors;
- Kannada fixtures and mock tests.

Acceptance:
- local model responds to a simple Kannada prompt;
- extraction returns validated schema for basic fixtures;
- invalid model output does not change conversation state;
- model endpoint is not public.

## M1 — Speech pipeline

### M1.1 ASR adapter

Deliverables:
- audio validation/normalization;
- IndicConformer service adapter;
- temporary-file handling and cleanup;
- transcription result schema;
- audio test fixtures and model health endpoint.

Acceptance:
- clean Kannada audio transcribes successfully on developer machine;
- invalid/corrupt/oversized audio rejected;
- raw audio deleted on all normal/error paths;
- model/checkpoint version and hardware recorded.

### M1.2 TTS adapter

Deliverables:
- Indic-TTS runtime isolated from API;
- Kannada text-to-audio endpoint/internal adapter;
- temporary generated-audio store and TTL cleanup;
- text-only fallback.

Acceptance:
- short Kannada response synthesizes and plays;
- failure returns text and explicit audio-unavailable status;
- exact model checkpoint licence and source recorded before distribution.

## M2 — NLU and normalization

Deliverables:
- intent taxonomy;
- agricultural slot schema;
- Kannada agriculture alias dictionaries;
- district/taluk/crop canonical lookup approach;
- acreage/gunta/hectare conversion module;
- confirmation flags and provenance.

Acceptance:
- utterance fixtures extract correct typed slots;
- ambiguous values remain unknown/proposed;
- fractions and unit conversion tests pass;
- no `verified` status can be supplied by the LLM.
- **Status:** COMPLETED. (See `docs/M2_AGRICULTURAL_UNDERSTANDING.md`, 121 tests passing, 87% coverage).

## M3 — Dialogue and context

Deliverables:
- explicit state machine;
- dynamic next-slot selection;
- confirmation/correction flows;
- context retrieval and summaries;
- PostgreSQL conversation/turn/slot persistence;
- optimistic locking for concurrent conversation turns.

Acceptance:
- multi-turn flow works with text fixtures and live voice;
- previously confirmed values are not requested again unnecessarily;
- correction invalidates/recomputes affected recommendation results;
- context is scoped to farmer and conversation.
- **Status:** COMPLETED. (See `docs/M3_DIALOGUE_AND_PERSISTENT_MEMORY.md`, 142 tests passing, 87% coverage).

## M4 — Scheme engine

Deliverables:
- validated scheme catalog schema;
- 5 reference records;
- rule interpreter with controlled operators;
- tri-state evaluator;
- immutable traces and rule versions;
- source provenance and stale-rule behavior;
- synthetic-only rules/fixtures approved by project owner.

Acceptance:
- truth tables pass;
- PM-KISAN and PMFBY remain `RULES_NOT_VERIFIED` until official rules are reviewed and encoded;
- all synthetic results show `DEMO_ONLY`;
- model cannot alter rule outcome.
- **Status:** COMPLETED. (See `docs/M4_SCHEME_INTELLIGENCE.md`, 165 tests passing, 87% coverage).

## M5 — Auth, authorization and privacy

Deliverables:
- farmer registration/login/refresh/logout;
- Argon2id password hashing;
- resource ownership checks;
- consent records and retention config;
- deletion workflow;
- secure audio lifecycle and redacted logs.

Acceptance:
- access-control/IDOR suite passes;
- farmer A cannot access farmer B data;
- deletion workflow removes linked data and audio/cache;
- input audio does not persist by default.
- **Status:** COMPLETED. (See `docs/M5_SECURITY_AND_PRIVACY.md`, 201 tests passing, 90% statement coverage).

## M6 — Frontend integration and network resilience

Deliverables:
- stable OpenAPI contract;
- voice/text turn endpoints;
- idempotency and job-status endpoint;
- authorized temporary audio response endpoint;
- CORS and browser auth integration;
- recovery test scenarios and frontend handoff.

Acceptance:
- separate frontend can complete one Kannada voice conversation end-to-end;
- duplicate retries do not create duplicate turns;
- disconnect/reconnect retrieves the same job result;
- text fallback works;
- TTS failure does not fail text response.

## M7 — Performance and production readiness

Deliverables:
- durable queue/broker and separate worker pools;
- Valkey/cache if justified;
- queue backpressure and rate limits;
- monitoring/metrics/health;
- Locust profiles and benchmark report;
- deployment and backup/restore documentation.

Acceptance:
- documented capacity test on named hardware;
- queue and worker failure recovery pass;
- no unbounded concurrency or memory blow-up;
- API instances can scale horizontally without local state;
- production cost/hardware needs are documented.

## Recommended order for first demo

1. M0.1 + M0.2.
2. M1.1 (ASR) + M1.2 (TTS) in isolated environments.
3. M2 + M3 with text fixtures before real audio is wired through.
4. M4 synthetic scheme path, with real scheme records blocked as unverified.
5. M5/M6 integration and privacy/security tests.
6. M7 only after baseline measurement.
