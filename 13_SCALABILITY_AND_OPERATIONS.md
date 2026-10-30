# 13 — Scalability, Capacity and Operations

## 1. Distinguish load types

The phrase “1,000 users” is insufficient as a capacity target. Distinguish:

1. 1,000 registered accounts;
2. 1,000 open browser sessions;
3. 1,000 simultaneous API calls;
4. 1,000 simultaneous audio uploads;
5. 1,000 concurrent ASR + LLM + TTS inference jobs.

The fifth workload is vastly more demanding. No software architecture can guarantee it without measured compute capacity.

## 2. Scaled architecture

```text
Browser clients
   -> Load balancer / TLS / WAF or gateway
   -> Stateless FastAPI instances
   -> PostgreSQL (system of record)
   -> Durable job broker
        -> ASR worker pool
        -> NLU/LLM worker pool
        -> TTS worker pool
   -> Valkey (cache, rate limits, ephemeral state)
   -> Metrics / logs / traces
```

Inference workers must be independently scaled and bounded. Do not run one loaded model copy per Uvicorn worker by accident; this can multiply RAM/VRAM consumption.

## 3. Queue and cache choices

- **MVP:** synchronous calls or a simple durable database job adapter for the initial vertical slice. Keep interface stable.
- **Scaled async candidate:** RabbitMQ + Celery (or another selected durable broker/worker combination) after compatibility/integration tests.
- **Cache:** Valkey is the preferred Redis-compatible cache candidate; BSD-3-Clause. Use it for ephemeral cache/rate limiting, not as source of truth.
- Pin exact versions and review licence terms at implementation time.

## 4. API scaling rules

- API instances are stateless.
- Do not store conversation state only in process memory.
- Use PostgreSQL pool sizing based on max connections and API replica count.
- Apply per-user and per-IP rate limits.
- Enforce audio upload caps and queue admission control.
- Return 429 for rate limit and 503/retryable when queue capacity is exhausted.
- Use request IDs and trace IDs across services.
- Keep model inference off the FastAPI event loop.

## 5. Worker scaling

Measure separately for ASR, LLM and TTS:

- model load memory;
- CPU and GPU utilization;
- average and p95 inference time;
- throughput per worker;
- queue wait;
- cold start and warm start;
- batch-size impact;
- audio duration distribution;
- memory leaks / model reload behavior.

Set concurrency per model based on measured memory. Prefer explicit worker semaphores and max-in-flight settings rather than unconstrained parallelism.

## 6. Backpressure

- Set maximum queue depth and maximum job age.
- Stop accepting more jobs when capacity threshold is reached.
- Give the UI a clear “busy, retry” state.
- Prioritize interactive jobs fairly; prevent a single farmer from monopolizing workers.
- Use separate queues or quotas for ASR, LLM and TTS if one stage starves another.

## 7. Reliability targets

Do not invent an SLA before hardware is selected. First establish a benchmark baseline. Report:

- API non-inference p50/p95/p99;
- each model stage p50/p95/p99;
- end-to-end voice-turn p50/p95/p99;
- queue wait;
- success/failure rate;
- requests per second and concurrent jobs;
- CPU, RAM, GPU/VRAM and database connections.

Initial test progression: 10, 25, 50, 100 concurrent sessions/jobs, then higher loads only while observing resource use. A 1,000-session test is not the same as a 1,000-simultaneous-inference test.

## 8. Observability

### Logs

Structured JSON logs with `request_id`, `job_id`, `turn_id`, component, model version, error code, duration, status. Never include raw audio, transcripts, prompts, tokens or phone numbers.

### Metrics

- request counts and latency by route;
- ASR/LLM/TTS latency and error counts;
- queue depth/oldest-job age;
- worker active/idle counts;
- DB pool usage and query latency;
- temp-audio deletion success/failure count (no filenames containing user IDs);
- rate-limits and auth failures;
- scheme evaluation outcome counts (aggregate only; do not expose personal details).

### Health

- liveness: process alive;
- readiness: dependencies needed to accept work;
- worker health: heartbeat/last success;
- model health: local endpoint available and configured model ready.

Do not make liveness depend on a slow model inference request.

## 9. Deployment

- use Docker/Compose for reproducible development;
- separate API, DB, broker and model services;
- mount model weights read-only where possible;
- model ports are private;
- persist PostgreSQL data with backups;
- pin images and dependencies;
- use health checks, resource limits and non-root containers where compatible;
- never commit secrets or large model weights.

## 10. Free-resource reality

The stack is based on open-source software and local inference. It is not an unlimited-free hosting plan. Public deployment, high-memory/GPU inference, network egress, storage, backups, monitoring and SMS authentication can incur cost. Build a local proof first and present capacity findings honestly.
