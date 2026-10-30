# 12 — Network Resilience and Offline Degradation

## 1. MVP principle

The first version is **offline-resilient, not fully offline-AI**. Browser assets and the last locally saved conversation state may remain available offline; server-hosted ASR, LLM, TTS and current scheme-rule evaluation require network access to the backend.

## 2. Client responsibilities (frontend team)

- use a service worker/PWA cache for application shell and static assets;
- maintain a visible `ONLINE`, `OFFLINE`, `RECONNECTING` state;
- preserve last acknowledged conversation state locally;
- show which items are cached and when they were last updated;
- do not silently queue or upload raw farmer audio later;
- only queue an audio upload if the farmer explicitly consents to delayed upload and the product owner approves an encrypted, expiring queue design;
- display pending/failed turns clearly;
- use idempotency keys and poll existing jobs after reconnection.

Local persistence of profile or transcripts must be minimized. Shared phones are common; local data should be protected, expire and be clearable. Do not persist refresh tokens in localStorage.

## 3. Three failure scenarios

### A. Connection is lost before upload

- keep the previous acknowledged conversation state;
- discard unsent audio by default;
- show offline state and offer text draft or retry when online;
- do not create a server turn.

### B. Connection is lost during upload or inference

- the client already has the same idempotency key/request ID;
- after reconnection, query job status or resubmit with the same key;
- backend returns the original request, not a duplicate turn;
- if the backend never accepted the job, create it once after retry;
- if processing was interrupted, job recovery marks it retryable and worker reclaims it safely.

### C. Connection is lost after response generation

- backend stores the completed response transactionally;
- client polls the existing job ID and retrieves the result;
- do not re-run inference for an already-completed job;
- temporary TTS audio may expire; client can request regenerated audio from stored assistant text if permitted.

## 4. Job state machine

```text
QUEUED -> PROCESSING -> COMPLETED
                    -> FAILED_RETRYABLE -> QUEUED
                    -> FAILED_FINAL
QUEUED -> CANCELLED
```

Use attempt count, lease/heartbeat, visibility timeout or lock timeout, bounded retries with exponential backoff and jitter. Never retry non-idempotent side effects without idempotency safeguards.

## 5. Idempotency requirements

- key scoped to authenticated farmer + endpoint;
- request body hash stored;
- same key/same body returns same request/turn;
- same key/different body returns 409;
- turn creation and idempotency record committed atomically;
- concurrent requests for same conversation use optimistic locking / one active mutating turn.

## 6. Timeout policy

Timeouts must be configurable per stage:

- audio upload;
- preprocessing;
- ASR;
- LLM extraction;
- scheme evaluation;
- TTS;
- total job age.

Use bounded retries. Do not automatically retry a slow model indefinitely; after the retry budget, return a recoverable error and preserve the previous conversation state.

## 7. Degraded modes

| Failure | User experience |
|---|---|
| Microphone blocked | Offer text input and browser permission instructions |
| ASR worker down | Keep job retryable; offer repeat/text mode |
| Poor/ambiguous transcript | Ask a targeted repeat/confirmation question |
| LLM unavailable | Do not update slots; offer retry or text-only help if safe |
| TTS unavailable | Deliver text response and show audio unavailable |
| Scheme rules stale | Say current rule information cannot be verified; do not recommend as current |
| Database unavailable | Do not claim state is saved; show retryable error |
| Queue unavailable | Reject new async work cleanly; do not spawn unbounded background tasks |
| Network offline | Use cached shell/state only; no current personalized scheme decision |

## 8. Cached scheme information

Any offline cache must show:

- last-updated/last-verified timestamp;
- whether it is real scheme information or demo content;
- that it may be stale;
- official portal reference.

Never present a cached old seasonal PMFBY notification as current.
