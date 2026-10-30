# 03 — System Architecture

## 1. Architecture style

Use a **modular monolith for business/API logic** with independently replaceable model adapters. For the first working slice, one FastAPI application may orchestrate the flow while ASR/TTS/LLM are local processes/services. Introduce separate inference workers and a durable queue as soon as real-time load or blocking operations require them. Do not begin with many microservices or Kubernetes.

## 2. Logical components

1. **API / Auth:** REST endpoints, authentication, request validation, authorization and API error model.
2. **Audio Gateway:** upload validation, audio normalization, temporary-file handling and cleanup.
3. **ASR Adapter:** IndicConformer primary; optional evaluated fallback.
4. **NLU Adapter:** LLM-based intent/slot extraction with JSON Schema/Pydantic validation.
5. **Normalizer:** Kannada vocabulary aliases, place/crop dictionaries and measurement conversion.
6. **Dialogue Manager:** deterministic state machine; selects next action and asks for missing information.
7. **Context Manager:** retrieves/stores farmer profile, slots, summary and limited recent messages.
8. **Scheme Registry:** immutable, versioned scheme data with source provenance.
9. **Eligibility Engine:** deterministic three-valued rule evaluation.
10. **Response Composer:** grounded explanation from engine output and official scheme content.
11. **TTS Adapter:** Indic-TTS candidate; produces transient response audio.
12. **Persistence:** PostgreSQL for accounts, farmer profile, conversation, turns, slot facts, jobs and recommendation traces.
13. **Queue/Cache:** RabbitMQ or equivalent for durable jobs; Valkey for transient cache/rate-limit/session data where useful.
14. **Observability:** structured logs without user content, metrics, traces and health checks.

## 3. End-to-end voice turn

```text
Farmer browser
  -> HTTPS audio upload + auth + idempotency key
  -> API validates identity, conversation ownership and audio constraints
  -> creates durable turn/job record
  -> audio adapter normalizes audio in temporary storage
  -> ASR returns transcript + available decoding metadata
  -> NLU extracts intent/slots as schema-constrained JSON
  -> normalizer maps canonical values and retains uncertainty/provenance
  -> dialogue manager merges with current conversation state
       -> if required info missing: select one follow-up question
       -> else: invoke deterministic scheme evaluation
  -> response composer creates grounded Kannada text
  -> TTS converts response text to speech (best-effort)
  -> store turn, slots, decision trace, status; do not store input audio
  -> client retrieves result/audio using authorized short-lived URL/endpoint
```

## 4. Trust boundaries

- Browser is untrusted. Treat audio, text, IDs, metadata and MIME declarations as attacker-controlled.
- LLM output is untrusted. Validate against strict schema and field allow-lists.
- Model processes are internal services. Do not expose Ollama, ASR or TTS ports publicly.
- Scheme catalog is trusted only after code review and provenance validation.
- The system service identity is private and cannot be impersonated by a farmer JWT.
- Database access must use least-privilege application credentials.

## 5. Deployment topology

### Local MVP

- FastAPI app.
- PostgreSQL.
- Ollama/Qwen3 4B.
- ASR process/service with IndicConformer.
- TTS process/service with Indic-TTS if operational setup passes.
- Docker Compose for API and database; model processes may run on host/WSL because ML dependencies/GPU access can be difficult inside Compose.

### Scaled deployment

- HTTPS reverse proxy/load balancer.
- Multiple stateless FastAPI instances.
- Durable queue (RabbitMQ recommended candidate) and bounded worker pools.
- Dedicated ASR, LLM and TTS inference processes/hosts sized from measured throughput.
- PostgreSQL managed or self-hosted with backups, connection pooler and monitoring.
- Valkey for cache/rate limits if needed.
- Object storage only if an explicitly approved audio-retention feature is added; none by default.

## 6. Failure isolation

- ASR failure: keep turn retryable; present a Kannada repeat prompt or text fallback.
- NLU failure: do not update slots; ask user to rephrase or retry.
- TTS failure: return text response with audio unavailable.
- Scheme engine failure: do not guess; return an explicit temporary failure and do not emit stale cached eligibility as current.
- Database failure: do not claim turn saved; return retryable service error.
- Broker failure: if queue cannot accept a job, return `503`/retryable; do not silently run unbounded in-request inference.

## 7. Data flow invariants

- Request is authenticated before inference.
- Conversation is verified to belong to farmer before loading context.
- Each turn has an idempotency key.
- Raw input audio lives only in a controlled temporary path and is deleted in `finally`/cleanup jobs.
- LLM never writes directly to the database.
- LLM never calls the scheme rule evaluator with free-form arguments; application code builds typed inputs.
- Rule evaluation output is immutable for a given profile snapshot and rule version.
- TTS output is transient by default.
