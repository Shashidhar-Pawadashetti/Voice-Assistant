# 09 — REST API Contract

**Base path:** `/api/v1`  
**Transport:** HTTPS in all non-local environments  
**Format:** JSON; audio endpoints use multipart/form-data  
**Authentication:** farmer access token; internal service authentication for worker-only endpoints  
**Versioning:** additive compatible changes within v1; breaking changes require `/v2`.

## 1. Standard response and errors

Success responses use documented Pydantic response models. Errors use:

```json
{
  "error": {
    "code": "AUDIO_UNSUPPORTED_FORMAT",
    "message": "The audio format is not supported.",
    "retryable": false,
    "request_id": "req_...",
    "details": {}
  }
}
```

Do not expose stack traces, model prompts, file-system paths or internal service URLs.

## 2. Authentication endpoints

Implemented in Milestone M5 (`app/api/v1/auth.py`):

### POST `/api/v1/auth/register`
Request:
```json
{
  "phone_number": "9876543210",
  "password": "StrongPassword!2026",
  "preferred_language": "kn",
  "consent_given": true
}
```
Response (`201 Created`):
```json
{
  "farmer": {
    "id": "uuid",
    "phone_number_masked": "+91 ******3210",
    "preferred_language": "kn",
    "account_status": "ACTIVE",
    "created_at": "2026-10-31T00:00:00Z",
    "last_login_at": "2026-10-31T00:00:00Z"
  },
  "tokens": {
    "access_token": "jwt_token_string",
    "refresh_token": "cryptographic_random_string",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### POST `/api/v1/auth/login`
Request:
```json
{
  "phone_number": "9876543210",
  "password": "StrongPassword!2026"
}
```
Response (`200 OK`):
```json
{
  "access_token": "jwt_token_string",
  "refresh_token": "cryptographic_random_string",
  "token_type": "bearer",
  "expires_in": 900
}
```
*Security Invariants:* Generic 401 error `"Invalid phone number or password"` preventing user enumeration. Constant-time dummy verify. Account lockout after 5 failed attempts for 15 minutes. Sliding-window IP rate limiting.

### POST `/api/v1/auth/refresh`
Request:
```json
{
  "refresh_token": "cryptographic_random_string"
}
```
Rotates refresh token and issues a new access token. If an already-rotated or revoked token is reused, the entire token family is revoked immediately.

### POST `/api/v1/auth/logout`
Header: `Authorization: Bearer <access_token>`  
Request body (optional): `{"refresh_token": "..."}`  
Revokes active refresh token(s) and logs audit event.

### GET `/api/v1/auth/me`
Header: `Authorization: Bearer <access_token>`  
Returns authenticated farmer profile and masked phone number.

### POST `/api/v1/auth/change-password`
Header: `Authorization: Bearer <access_token>`  
Request: `{"old_password": "...", "new_password": "..."}`  
Changes password using Argon2id, revokes all active refresh tokens, and requires re-login.

## 3. Conversation endpoints

### POST `/conversations`

Creates a conversation.

Request:
```json
{"language": "kn", "input_mode": "VOICE"}
```

Response:
```json
{
  "conversation_id": "uuid",
  "status": "ACTIVE",
  "state": "DISCOVERING_INTENT",
  "created_at": "2026-10-30T12:00:00Z"
}
```

### GET `/conversations`

List only the authenticated farmer's conversations. Paginate.

### GET `/conversations/{conversation_id}`

Return conversation metadata, current dialogue state and current allowed summary. Do not return raw audio or another farmer's content.

*(Implemented in `/api/v1/conversations/{conversation_id}` as part of Milestone M3 with BOLA verification and optimistic concurrency).*

### DELETE `/conversations/{conversation_id}`

Delete or schedule deletion of that farmer's conversation and linked content according to retention policy. Must verify ownership.

## 4. Turn endpoints

### POST `/conversations/{conversation_id}/turns/audio`

Headers:
- `Authorization: Bearer <access-token>`
- `Idempotency-Key: <opaque-unique-key>`

Multipart fields:
- `audio`: audio binary;
- `language`: optional, default `kn`;
- `client_turn_id`: optional frontend-generated UUID.

Response for async path:
```json
{
  "request_id": "uuid",
  "turn_id": "uuid",
  "conversation_id": "uuid",
  "status": "QUEUED",
  "status_url": "/api/v1/jobs/uuid"
}
```

### POST `/conversations/{conversation_id}/turns/text`

Request:
```json
{
  "text": "ನಾನು ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ಜೋಳ ಬೆಳೆಯುತ್ತೇನೆ",
  "language": "kn",
  "client_turn_id": "uuid"
}
```

Apply the exact same dialogue/NLU validation and idempotency logic as audio turns. Mark input source as `TEXT`, not `VOICE`.

## 5. Job endpoint

### GET `/jobs/{request_id}`

Response statuses:

- `QUEUED`
- `PROCESSING`
- `COMPLETED`
- `FAILED_RETRYABLE`
- `FAILED_FINAL`
- `CANCELLED`

Only the owning farmer may retrieve a user job. Internal worker endpoints require machine identity and are not exposed to browsers.

Completed response:
```json
{
  "request_id": "uuid",
  "status": "COMPLETED",
  "result": {
    "turn_id": "uuid",
    "transcript": {
      "text": "ನಾನು ನಾಲ್ಕು ಎಕರೆ ಜಮೀನು ಹೊಂದಿದ್ದೇನೆ",
      "language": "kn",
      "requires_confirmation": true
    },
    "assistant": {
      "text": "ನೀವು ನಾಲ್ಕು ಎಕರೆ ಜಮೀನು ಹೊಂದಿದ್ದೀರಿ ಎಂದು ನಾನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ. ಸರಿಯೇ?",
      "audio_url": "/api/v1/audio-responses/uuid"
    },
    "dialogue": {
      "state": "CONFIRMING_CRITICAL_FACTS",
      "next_required_slot": "land_area_confirmation"
    },
    "recommendations": []
  }
}
```

### GET `/audio-responses/{audio_id}`

Return only if the current farmer owns the conversation/turn associated with the audio. Use short TTL and private caching rules. Return 404/410 when expired/deleted.

## 6. Recommendations

### GET `/conversations/{conversation_id}/recommendations`

Return recommendation runs and traces belonging to that conversation. Example item:

```json
{
  "scheme_id": "PMFBY",
  "classification": "REAL_GOVERNMENT",
  "outcome": "RULES_NOT_VERIFIED",
  "official_verification_required": true,
  "demo_only": false,
  "matched_conditions": [],
  "failed_conditions": [],
  "unknown_conditions": [
    {"condition_id": "current_notified_crop_area", "required_slot": "notified_area_status"}
  ],
  "rule_version": "0.0.0",
  "verification_status": "INCOMPLETE",
  "sources": [{"title": "PMFBY official portal", "url": "https://pmfby.gov.in/"}]
}
```

If `verification_status` is `INCOMPLETE`, the outcome must be `RULES_NOT_VERIFIED`; condition-level unknowns may be included as diagnostic metadata but must not be presented as a verified eligibility evaluation.

## 7. Farmer privacy and data rights (DPDP Act 2023)

Implemented in Milestone M5 (`app/api/v1/privacy.py`):

### GET `/api/v1/privacy/export`
Header: `Authorization: Bearer <access_token>`  
Returns a structured, machine-readable export of all records belonging to the authenticated farmer:
- Farmer account metadata (language, registration date, last login)
- Profile attributes and agricultural facts
- Notice and consent history
- Conversation sessions, turns, and slot values
- Historical scheme recommendation runs and explanation traces
*Invariant:* Plaintext passwords, Argon2id hashes, and symmetric encryption keys are never exported.

### POST `/api/v1/privacy/delete`
Header: `Authorization: Bearer <access_token>`  
Request:
```json
{
  "password": "FarmerPassword!2026",
  "reason": "Optional reason for account deletion"
}
```
Requires password confirmation. Atomically executes verified erasure:
- Purges all farmer response audio files from the ephemeral audio store
- Deletes conversation sessions, turns, and slots
- Deletes farmer profile records and refresh tokens
- Withdraws all active consents
- Anonymizes recommendation audit records by redacting profile snapshots
- Deactivates farmer account (`account_status = 'DELETED'`), scrambles phone blind index, and overwrites credentials
- Returns a completion receipt with `records_erased` summary and `deletion_request_id`

## 8. Scheme catalog & recommendation endpoints

Implemented in Milestone M4:
- `GET /api/v1/schemes`: Lists approved scheme catalog summaries with `classification`, `verification_status`, and `demo_only` indicators. Filterable by `classification` and `category`.
- `GET /api/v1/schemes/{scheme_id}`: Full scheme specification, eligibility conditions, exclusions, required documents, application portal, and evidence references.
- `POST /api/v1/conversations/{conversation_id}/recommendations`: Triggers deterministic three-valued evaluation of applicable schemes against the conversation profile. Saves immutable `recommendation_runs` in PostgreSQL. Enforces `x-farmer-id` BOLA ownership.
- `GET /api/v1/conversations/{conversation_id}/recommendations`: Returns chronological audit traces for all previous recommendation runs of that conversation.

No public POST/PUT/PATCH/DELETE scheme management endpoints exist; scheme releases are reviewed, version-controlled code/seed releases.

## 9. Health endpoints

- `GET /health/live`: API process is alive; no expensive dependency check.
- `GET /health/ready`: dependencies needed to accept work are ready; do not expose secrets/version internals.

## 10. Idempotency and concurrency

- `Idempotency-Key` scoped to farmer + endpoint; retain for at least the maximum retry window.
- Same key + same payload returns the original turn/job result.
- Same key + different payload returns `409 IDEMPOTENCY_KEY_REUSED`.
- A conversation should have at most one active state-mutating turn at a time, unless optimistic concurrency/versioning is implemented. Return `409 CONVERSATION_TURN_IN_PROGRESS` for concurrent conflicting turns.
- Use `conversation_version` or compare-and-swap update to avoid lost updates.

## 11. Rate limits and bounds

Configurable per farmer/IP limits for login, audio upload, text turns and polling. Initial audio size/duration bounds are configuration values, not hard-coded assumptions. Return `429 RATE_LIMITED` with retry metadata.

## 12. API contract ownership

The backend team must publish OpenAPI JSON from FastAPI. The website team should integrate against that contract and not rely on private Python functions or direct model ports.

## 13. Frontend client integration (Milestone M6)

The farmer-facing Progressive Web App (PWA) in `frontend/` integrates directly with these endpoints:
- **Authentication**: `frontend/src/services/auth.ts` manages login, registration, token refresh, and session restoration.
- **Voice & Turn Dialogue**: `frontend/src/services/conversation.ts` formats multipart audio uploads and text turns with unique `client_turn_id` idempotency keys and `expected_version` optimistic locking.
- **Audio Retrieval**: `frontend/src/services/audio.ts` uses authenticated fetch to pass `Authorization: Bearer <token>` to `GET /api/v1/voice/audio/{id}` and generates temporary local Blob URLs (`URL.createObjectURL`).
- **Scheme Recommendations**: `frontend/src/services/scheme.ts` consumes recommendation results and transparent explanation traces.
- **DPDP Rights**: `frontend/src/services/privacy.ts` provides machine-readable export and password-verified erasure.
