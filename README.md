# Krishi Mitra — AI Developer Handoff

**Document set:** 1.0  
**Prepared:** 30 October 2026  
**Product:** Krishi Mitra — Kannada voice-first farmer scheme assistant  
**Primary implementer:** Antigravity CLI developer agent  
**Project boundary:** AI/backend subsystem. The website frontend is being built by a separate team.

## Purpose

This folder is the authoritative implementation handoff for the Krishi Mitra AI subsystem. Read it before changing code. It converts the product challenge into requirements, architecture, contracts, safety rules, data governance, testing criteria and an ordered implementation plan.

The system must let a farmer speak naturally in Kannada, including regional vocabulary and Kannada-English code-mixing; collect agricultural facts over multiple turns; ask only relevant follow-up questions; and return explainable, source-backed scheme suggestions. It must never present an unverified match as government approval or fabricate scheme rules.

## Read these documents in order

Start with [`START_PROMPT_FOR_ANTIGRAVITY.md`](START_PROMPT_FOR_ANTIGRAVITY.md) for a ready-to-paste first instruction to Antigravity. Then read the numbered documents below.

1. [`00_EXECUTION_ORDER.md`](00_EXECUTION_ORDER.md) — mandatory agent workflow and precedence.
2. [`01_PROJECT_BRIEF.md`](01_PROJECT_BRIEF.md) — product goal, scope and constraints.
3. [`02_PRODUCT_REQUIREMENTS.md`](02_PRODUCT_REQUIREMENTS.md) — functional and non-functional requirements.
4. [`03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md) — component boundaries and request flow.
5. [`04_ARCHITECTURE_DECISIONS.md`](04_ARCHITECTURE_DECISIONS.md) — decisions that must not be casually changed.
6. [`05_VOICE_AI_PIPELINE.md`](05_VOICE_AI_PIPELINE.md) — ASR, language understanding, LLM and TTS.
7. [`06_DIALOGUE_AND_MEMORY.md`](06_DIALOGUE_AND_MEMORY.md) — turn management, slots, context and state machine.
8. [`07_SCHEME_ENGINE_AND_GOVERNANCE.md`](07_SCHEME_ENGINE_AND_GOVERNANCE.md) — deterministic rules, three-valued logic and governance.
9. [`08_SCHEME_CATALOG_SEED.md`](08_SCHEME_CATALOG_SEED.md) — five reference schemes and what may/may not be asserted.
10. [`09_API_CONTRACT.md`](09_API_CONTRACT.md) — frontend/backend interface.
11. [`10_DATA_MODEL.md`](10_DATA_MODEL.md) — PostgreSQL entities and constraints.
12. [`11_SECURITY_AND_PRIVACY.md`](11_SECURITY_AND_PRIVACY.md) — authentication, authorization, data minimization and retention.
13. [`12_RESILIENCE_AND_OFFLINE.md`](12_RESILIENCE_AND_OFFLINE.md) — network failure, retries and PWA coordination.
14. [`13_SCALABILITY_AND_OPERATIONS.md`](13_SCALABILITY_AND_OPERATIONS.md) — queueing, workers, capacity and observability.
15. [`14_TEST_AND_EVALUATION.md`](14_TEST_AND_EVALUATION.md) — model evaluation, test plan and release gates.
16. [`15_IMPLEMENTATION_PLAN.md`](15_IMPLEMENTATION_PLAN.md) — milestone plan and deliverables.
17. [`16_LOCAL_DEVELOPMENT_SETUP.md`](16_LOCAL_DEVELOPMENT_SETUP.md) — Windows/WSL local environment.
18. [`17_ANTIGRAVITY_BUILD_INSTRUCTIONS.md`](17_ANTIGRAVITY_BUILD_INSTRUCTIONS.md) — direct instructions for the coding agent.
19. [`18_OPEN_QUESTIONS_AND_RISKS.md`](18_OPEN_QUESTIONS_AND_RISKS.md) — unresolved facts and risk register.
20. [`19_GLOSSARY_AND_REFERENCES.md`](19_GLOSSARY_AND_REFERENCES.md) — terminology and primary sources.

## The non-negotiable product rules

- **Voice-first:** speech interaction is the product's central workflow, not a microphone added to a generic text bot.
- **Kannada-first:** optimize and evaluate spoken Kannada, including regional accents and code-mixed language.
- **Rules decide eligibility:** the LLM extracts and explains; deterministic, versioned Python rules evaluate schemes.
- **No false entitlements:** return a potential match or an information-needed result, never a promise of approval, payment or benefit.
- **Unknown is a first-class state:** missing/unverified facts must not be silently assumed.
- **Privacy by default:** do not persist raw farmer audio by default; do not send data to third-party AI APIs in the initial architecture.
- **No admin role or admin interface:** only a farmer identity and an internal system service identity. Scheme catalog updates are code-reviewed releases, not public admin CRUD.
- **Free software is not free compute:** local/open-source software is the default, but production hardware, bandwidth and hosting may cost money. Do not promise 1,000 simultaneous voice-inference requests without load-test evidence.

## Current decisions at a glance

| Area | Decision |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Main LLM candidate | Qwen3 4B through local Ollama for MVP; must pass Kannada evaluation gate |
| ASR primary | AI4Bharat IndicConformer Kannada model |
| ASR fallback | Faster-Whisper is an experiment candidate only; do not route production traffic to it until Kannada benchmarked |
| TTS primary candidate | AI4Bharat Indic-TTS Kannada checkpoint; checkpoint licence and operational compatibility must be verified before distribution/deployment |
| Dialogue | Deterministic Python state machine + validated LLM extraction |
| Eligibility | Custom deterministic rule engine with TRUE/FALSE/UNKNOWN logic |
| Database | PostgreSQL; use a currently supported major release |
| Cache | Valkey (BSD-3-Clause) where useful; not required for the first vertical slice |
| Async jobs | RabbitMQ/Celery or a documented equivalent after synchronous MVP; hide behind job interface |
| API | Versioned REST; frontend can poll job status for MVP |
| Deployment | Docker/Compose for local development; production topology later |

## Milestone Implementation Status

- **M0 (Foundation & Schema-Constrained Extraction):** Complete. FastAPI backend, PostgreSQL 16 models & Alembic migrations, safe JSON structured logging with PII scrubbing, Ollama Qwen3 4B adapter with schema validation and bounded retry.
- **M1 (Speech Pipeline & Voice Orchestration):** Complete. Audio validation/normalization (16 kHz mono WAV via FFmpeg), AI4Bharat IndicConformer ASR adapter, Indic-TTS adapter with numeral expansion, ephemeral audio lifecycle, end-to-end voice pipeline. See [`docs/M1_SPEECH_PIPELINE.md`](docs/M1_SPEECH_PIPELINE.md).
- **M2 (Agricultural Understanding & Normalization):** Complete. Versioned Kannada agricultural vocabulary (`2026.10.1`), canonical Karnataka geographic hierarchy (31 districts & notified taluks), exact Decimal land normalization, tenure classification & provenance, natural Kannada correction handling, and multi-turn profile assembly without LLM eligibility calculation. See [`docs/M2_AGRICULTURAL_UNDERSTANDING.md`](docs/M2_AGRICULTURAL_UNDERSTANDING.md).
- **Current Test Suite:** 121 passing tests, 87% coverage.

## Change control

If implementation needs a decision that conflicts with these documents, the agent must:

1. explain the conflict and why a change is necessary;
2. propose an Architecture Decision Record (ADR) update;
3. wait for explicit project-owner approval before replacing a locked decision, unless the current implementation is technically impossible or unsafe;
4. record the selected alternative, licence, operational impact and migration path.

Never invent government eligibility conditions, official integrations, credentials, API access or production capacity.
