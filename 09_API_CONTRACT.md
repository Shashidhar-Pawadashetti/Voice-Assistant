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

### POST `/auth/register`

Request:

```json
{
  "phone_number": "+91XXXXXXXXXX",
  "password": "user-supplied-strong-password",
  "preferred_language": "kn",
  "consent_version": "privacy-notice-1.0"
}
```

The example phone is a placeholder. Validate and normalize phone format; do not log password/phone. Hash password using Argon2id. Do not imply phone ownership is verified unless an OTP/provider flow exists.

### POST `/auth/login`

Request:

```json
{"phone_number": "+91XXXXXXXXXX", "password": "..."}
```

Return short-lived access token and secure refresh mechanism. Preferred browser pattern: access token kept in memory; refresh token in `HttpOnly`, `Secure`, `SameSite` cookie. Configure CORS/CSRF protection for actual frontend origin.

### POST `/auth/refresh`, POST `/auth/logout`, GET `/me`

Refresh token rotation, revoke on logout, return minimal farmer profile. Every response is scoped to the authenticated farmer.

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

## 7. Farmer data deletion

### DELETE `/me/data`

Require recent re-authentication or another appropriate confirmation. Return a deletion request ID and status if deletion is asynchronous. The service must delete/anonymize data across all linked tables, cached items, temporary files and backups according to the approved retention/deletion policy. Do not report “deleted” until the workflow completes.

## 8. Scheme catalog read endpoint

Optional: `GET /schemes` exposes only approved display metadata and sources. It must not expose internal draft rules unless deliberately intended. No POST/PUT/PATCH/DELETE scheme endpoint is permitted in MVP.

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
