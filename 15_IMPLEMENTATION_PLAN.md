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
- **Status:** COMPLETED. (See `docs/M6_FRONTEND_INTEGRATION.md`, React + Vite PWA built in `frontend/`, 7 automated frontend tests passing, 201 backend tests passing).

## M7 — Performance and production readiness

Deliverables:
- multi-stage containerized deployment (`Dockerfile`, `frontend/Dockerfile`, `nginx/`);
- distributed Redis sliding-window rate limiting and token revocation;
- in-flight concurrency-safe refresh token rotation lock;
- JTI denylisting and epoch token invalidation;
- cryptographic key separation (`ENCRYPTION_KEY`, `BLIND_INDEX_KEY`) with rotation fallback;
- queue backpressure, ASGI body size caps (15MB voice, 2MB general), and OWASP security headers;
- automated backup, SHA-256 verification, and safe restore utility (`scripts/backup_restore.py`);
- multi-tier load simulation suite and latency benchmark (`scripts/load_test_simulation.py`);
- 4-region Kannada linguistic evaluation across North, South, Coastal, and Kalyana Karnataka (`scripts/evaluate_kannada_pipeline.py`);
- comprehensive production readiness audit, deployment runbook, security review, load report, linguistic evaluation, and farmer pilot operations checklist.

Acceptance:
- 100% test pass: 209 backend tests passing, 10 frontend automated tests passing;
- production PWA bundle built with zero TypeScript compilation errors;
- multi-tier concurrency load benchmarked (Tier 1 p50=184ms, Tier 2 p50=715ms, Tier 3 p50=2489ms);
- linguistic benchmark passes: WER 7.29%, CER 1.38%, Intent Accuracy 100%, Slot F1 93.20%, native TTS MOS 4.25 / 5.0;
- horizontal scaling ready: zero process-local state for authentication or rate limiting;
- full DPDP Act 2023 compliance verified (consent logging, portability export, verified erasure, regulatory retention).
- **Status:** COMPLETED. (See `docs/M7_PRODUCTION_READINESS.md`, `docs/M7_DEPLOYMENT_RUNBOOK.md`, `docs/M7_SECURITY_REVIEW.md`, `docs/M7_LOAD_TEST_REPORT.md`, `docs/M7_KANNADA_EVALUATION_REPORT.md`, `docs/M7_PILOT_CHECKLIST.md`).

## M8 — Controlled Farmer Pilot & Field Validation

Deliverables:
- Staging pre-flight validation suite verifying live PostgreSQL 16, Redis 7, OWASP security headers, BOLA isolation, key separation & dual-key rotation fallback, DPDP verified erasure, and isolated database restoration drill (`scripts/validate_staging_release.py` generating `docs/M8_STAGING_VALIDATION_AUDIT.md`);
- Automated synthetic cohort simulation harness evaluating 20 predefined fixtures across 11 tasks and 294 assertions with zero skips (`scripts/run_pilot_field_trial.py` generating `docs/M8_AUTOMATED_VALIDATION_REPORT.md` and `docs/m8_automated_validation_metrics.json`);
- DPDP Act 2023 compliant real-world field pilot evidence protocol, recruitment criteria, facilitator guardrails, and incident response (`docs/M8_REAL_FIELD_PILOT_PROTOCOL.md`);
- Consented farmer usability survey instrument and research anonymization template (`docs/M8_FARMER_FEEDBACK_TEMPLATE.md`);
- Corrected linguistic design requirements and illustrative dialogue analysis with zero fabricated quotes (`docs/M8_FARMER_FEEDBACK.md`);
- Agricultural domain and scheme governance validation report verifying PM-KISAN, PMFBY, Raitha Siri, tenant exclusions, and synthetic demo isolation (`docs/M8_SCHEME_VALIDATION_REPORT.md`);
- Reliability, performance, and resilience report detailing in-process ASGI latencies (p50=81.7ms, p95=198.7ms), audio lifecycle, and network drop idempotency (`docs/M8_RELIABILITY_REPORT.md`);
- Staged release decision establishing Gate 1 (Automated simulation certified passed), Gate 2 (Supervised micro-pilot N=10-15 authorized to commence), and Gate 3 (100-farmer rollout blocked/unauthorized without real field data) (`docs/M8_RELEASE_DECISION.md`).

Acceptance:
- 100% staging pre-flight checks pass against live PostgreSQL 16 and Redis 7 services (`scripts/validate_staging_release.py`);
- 100% automated scenario assertion completion rate across 20 synthetic fixtures (294/294 assertions passed cleanly, 0 skipped);
- In-process ASGI latency meets performance targets (median p50 = 81.7ms < 500ms);
- Deterministic scheme governance verified: zero unauthorized government entitlement approvals, tenant farmers barred from owner-only subsidies, synthetic schemes strictly tagged `DEMO_ONLY`;
- 100% idempotent recovery from simulated network interruptions using client turn IDs;
- Ephemeral audio files securely isolated to owners and purged within TTL;
- Full DPDP Act 2023 compliance verified: self-service data portability export and cryptographic account erasure;
- Strict prohibition against fabricating real participants, interviews, consent, or field observations enforced across all repository documentation.
- **Status:** COMPLETED & AUDITED under M8.6 Evidence Integrity. (See `docs/M8_AUTOMATED_VALIDATION_REPORT.md`, `docs/M8_STAGING_VALIDATION_AUDIT.md`, `docs/M8_REAL_FIELD_PILOT_PROTOCOL.md`, `docs/M8_FARMER_FEEDBACK_TEMPLATE.md`, `docs/M8_FARMER_FEEDBACK.md`, `docs/M8_RELEASE_DECISION.md`).

## Recommended order for first demo

1. M0.1 + M0.2.
2. M1.1 (ASR) + M1.2 (TTS) in isolated environments.
3. M2 + M3 with text fixtures before real audio is wired through.
4. M4 synthetic scheme path, with real scheme records blocked as unverified.
5. M5/M6 integration and privacy/security tests.
6. M7 only after baseline measurement.
