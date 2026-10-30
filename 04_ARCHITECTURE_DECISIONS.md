# 04 — Architecture Decision Records

Status values: **Accepted** means implement as written for MVP; **Provisional** means build behind an interface and measure before treating as production-fixed.

## ADR-001 — Python FastAPI backend

**Status:** Accepted  
**Decision:** Build AI backend in Python 3.11+ with FastAPI, Pydantic v2 and SQLAlchemy 2.x.  
**Reason:** Python has the relevant ML ecosystem; FastAPI provides typed API contracts and OpenAPI docs.  
**Consequences:** Keep blocking model inference out of the event loop; call separate model processes or bounded worker executors.

## ADR-002 — Modular monolith first

**Status:** Accepted  
**Decision:** Keep domain/API logic in one modular backend; separate inference runtime processes only where dependency isolation, GPU memory or load isolation requires it.  
**Reason:** Hackathon team size and debugging needs do not justify distributed microservices at the start.  
**Consequences:** Strict module boundaries and interfaces are required to permit later extraction.

## ADR-003 — Kannada ASR: IndicConformer

**Status:** Provisional until benchmark gate  
**Decision:** IndicConformer Kannada checkpoint is the primary ASR candidate. The project documents 22 Indian language models including Kannada and lists MIT licence for the repository.  
**Reason:** Indian-language-specific ASR and published Kannada checkpoint.  
**Consequences:** Must verify inference dependencies, checkpoint hash, model terms and actual accent/noise performance. Do not claim universal dialect accuracy.

## ADR-004 — ASR fallback policy

**Status:** Accepted  
**Decision:** Faster-Whisper is an experimental comparison/fallback candidate only. Enable automatically only after measured Kannada accuracy and confidence/trigger criteria are documented.  
**Reason:** A fallback that is weaker or gives different critical numbers can make the result less safe.  
**Consequences:** First fallback is repeat/clarify; model fallback is optional after benchmark.

## ADR-005 — Text LLM: Qwen3 4B via Ollama

**Status:** Provisional until Kannada eval gate  
**Decision:** Use `qwen3:4b` for local MVP NLU and short response composition. Keep model ID configurable. Qwen's published language list includes Kannada; the Ollama library publishes the 4B tag. Qwen3-4B model card identifies Apache-2.0.  
**Reason:** A locally runnable, multilingual model without a paid API dependency.  
**Consequences:** Evaluate real Kannada and code-mixed performance; exact quantization/variant matters; record model digest. Avoid reasoning mode for routine extraction if slower. The model is not the source of scheme truth.

## ADR-006 — Structured output, not free-form parsing

**Status:** Accepted  
**Decision:** Use Ollama JSON Schema structured outputs where supported, followed by Pydantic validation and semantic validation.  
**Reason:** Reliable extraction contract.  
**Consequences:** Invalid/contradictory output is retried once or handled as extraction failure; never accepted by regex-only best effort.

## ADR-007 — Kannada TTS: AI4Bharat Indic-TTS

**Status:** Provisional until checkpoint/legal/runtime gate  
**Decision:** Evaluate the Kannada Indic-TTS checkpoint. The project states Kannada is among supported languages and its repository exposes an MIT code licence; checkpoint/weights and dataset rights must be verified separately.  
**Reason:** Kannada-specific speech synthesis.  
**Consequences:** Isolate in a separate environment/service; if not viable, keep text response working and evaluate another legally usable local TTS option before substituting.

## ADR-008 — Deterministic eligibility engine

**Status:** Accepted  
**Decision:** Scheme conditions are data-driven, versioned and evaluated by Python rules. LLM has no authority to approve/reject eligibility. Use TRUE/FALSE/UNKNOWN condition results.  
**Reason:** Explainability, reproducibility and reduced hallucination risk.  
**Consequences:** Scheme data must cite sources and support effective dates, unknowns and exclusions.

## ADR-009 — PostgreSQL persistence

**Status:** Accepted  
**Decision:** PostgreSQL is the system of record. Use relational tables for entities and JSONB only for flexible structured details where justified.  
**Reason:** Transactional consistency, ownership constraints and auditable rule output.  
**Consequences:** Use migrations, indexes, foreign keys, connection pooling and tested deletion workflows. Target a currently supported PostgreSQL release; PostgreSQL 18 is current as of the document date.

## ADR-010 — Cache/queue licensing

**Status:** Accepted with implementation split  
**Decision:** Do not assume all Redis versions are permissively open-source. Use Valkey for cache-compatible workloads (BSD-3-Clause). Use RabbitMQ (MPL 2.0) as the durable broker candidate for scaled asynchronous jobs, or retain a DB-backed job adapter for the first vertical slice.  
**Reason:** Respect the free/open-source requirement and avoid ambiguous Redis version licensing.  
**Consequences:** Abstract queue and cache; pin exact versions and verify transitive licences.

## ADR-011 — No admin identity or public scheme mutation

**Status:** Accepted  
**Decision:** Only farmer human accounts exist. Internal SYSTEM service principal is machine-to-machine only. Scheme rules are updated via reviewed data/code releases.  
**Reason:** User requirement and protection against unreviewed entitlement logic.  
**Consequences:** No admin routes, UI or broad database credentials in the application.

## ADR-012 — No raw audio retention by default

**Status:** Accepted  
**Decision:** Raw farmer input audio is transient, deleted after inference and not backed up. Store structured slots and limited transcript/history only under explicit consent and documented retention.  
**Reason:** Voice privacy and data minimization.  
**Consequences:** Temporary directory cleanup, failure cleanup, retention tests and no audio in logs.

## ADR-013 — No vector database in MVP

**Status:** Accepted  
**Decision:** Use relational queries and PostgreSQL JSONB for five scheme records and structured conversation state. Do not add RAG/vector infrastructure until there is a measured content-retrieval need.  
**Reason:** Current scope is structured, small and rule-driven.  
**Consequences:** Scheme evidence is fetched via deterministic records and source URLs, not embeddings.

## ADR-014 — Offline degradation, not offline AI

**Status:** Accepted  
**Decision:** Frontend preserves last known state and recovers jobs; cloud/local-server AI calls require connectivity to the server. Full device-side offline ASR/LLM/TTS is out of MVP.  
**Reason:** Model footprint and device constraints.  
**Consequences:** Clearly distinguish cached guidance from current personalized recommendations.
