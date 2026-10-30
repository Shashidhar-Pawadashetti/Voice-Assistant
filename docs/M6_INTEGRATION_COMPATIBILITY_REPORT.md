# M6 — Frontend & Backend Integration Compatibility Report

**Document Version:** 1.0  
**Date:** 31 October 2026  
**Backend Baseline:** M5 commit `d4668c07b7445f2be7a03ecbabc3e6b59d2cb05a`  
**Purpose:** Pre-implementation architectural audit and contract verification for the Krishi Mitra Farmer Frontend (PWA).

---

## 1. Baseline Audit & Repository Status

1. **Frontend Directory Status**:
   - The repository root currently contains the FastAPI backend, Alembic migrations, database models, tests, and milestone architecture documentation (M0–M5).
   - No frontend code, web client, or HTML/JS build configuration was committed prior to Milestone M6.
   - A modern React + Vite TypeScript Progressive Web App (PWA) will be created in `frontend/` to fulfill the M6 directive.

2. **Backend API Readiness**:
   - All required REST endpoints for authentication, conversations, multi-turn dialogue, voice input/output, scheme recommendation, and DPDP privacy rights are fully implemented, tested, and operational in `app/api/v1/`.
   - OpenAPI 3.1.0 specification generated and verified against Pydantic schema models.

---

## 2. API Contract & Schema Verification

| Subsystem | Endpoint | HTTP Method | Request Payload | Response Schema | Auth Invariant |
|---|---|---|---|---|---|
| **Health** | `/health/live`, `/health/ready` | `GET` | None | `LivenessResponse`, `ReadinessResponse` | Public |
| **Auth** | `/api/v1/auth/register` | `POST` | `RegisterRequest` (`phone_number`, `password`, `preferred_language`, `consent_given`) | `RegisterResponse` (201 Created) | Public (Rate-limited: 5 / 15m) |
| **Auth** | `/api/v1/auth/login` | `POST` | `LoginRequest` (`phone_number`, `password`) | `TokenResponse` (200 OK) | Public (Rate-limited + Lockout) |
| **Auth** | `/api/v1/auth/refresh` | `POST` | `RefreshTokenRequest` (`refresh_token`) | `TokenResponse` (200 OK) | Public (Single-use rotation) |
| **Auth** | `/api/v1/auth/logout` | `POST` | `LogoutRequest` (optional `refresh_token`) | `{"message": "..."}` | `Bearer <access_token>` |
| **Auth** | `/api/v1/auth/me` | `GET` | None | `FarmerResponse` (200 OK) | `Bearer <access_token>` |
| **Auth** | `/api/v1/auth/change-password` | `POST` | `ChangePasswordRequest` (`old_password`, `new_password`) | `{"message": "..."}` | `Bearer <access_token>` |
| **Conversations** | `/api/v1/conversations/active` | `GET` | None | `ConversationResponse` (or 404) | `Bearer <access_token>` |
| **Conversations** | `/api/v1/conversations` | `POST` | `CreateConversationRequest` (`language="kn"`, `initial_intent`) | `ConversationResponse` (201 Created) | `Bearer <access_token>` |
| **Conversations** | `/api/v1/conversations` | `GET` | Query (`status`, `limit`, `offset`) | `ConversationListResponse` | `Bearer <access_token>` |
| **Conversations** | `/api/v1/conversations/{id}` | `GET` | Path `id` (UUID) | `ConversationResponse` | `Bearer <access_token>` (BOLA) |
| **Dialogue Turn** | `/api/v1/conversations/{id}/turns/text` | `POST` | `TurnTextRequest` (`text`, `language`, `client_turn_id`, `expected_version`) | `TurnResponse` | `Bearer <access_token>` (BOLA + Idempotent) |
| **Dialogue Turn** | `/api/v1/conversations/{id}/turns/voice`| `POST` | Multipart Form (`file`, `language`, `client_turn_id`) | `TurnResponse` | `Bearer <access_token>` (BOLA + Idempotent) |
| **Voice Audio** | `/api/v1/voice/audio/{audio_id}` | `GET` | Path `audio_id` (alphanumeric) | Binary `audio/wav` | `Bearer <access_token>` (Owner-bound) |
| **Schemes** | `/api/v1/schemes` | `GET` | Query (`classification`, `category`) | `List[SchemeSummaryResponse]` | Public / Verified Catalog |
| **Schemes** | `/api/v1/schemes/{id}` | `GET` | Path `scheme_id` | `SchemeDetailResponse` | Public / Verified Catalog |
| **Recommendations** | `/api/v1/conversations/{id}/recommendations` | `POST` | Path `conversation_id` | `RecommendationEvaluationResponse` | `Bearer <access_token>` (BOLA) |
| **Recommendations** | `/api/v1/conversations/{id}/recommendations` | `GET` | Path `conversation_id` | `RecommendationRunResponse` | `Bearer <access_token>` (BOLA) |
| **Privacy** | `/api/v1/privacy/export` | `GET` | None | `DataExportResponse` | `Bearer <access_token>` (Full machine-readable) |
| **Privacy** | `/api/v1/privacy/delete` | `POST` | `DeletionRequestPayload` (`password`, `reason`) | `DeletionResponse` | `Bearer <access_token>` (Password confirmed) |

---

## 3. Critical Contract Nuances & Frontend Implementation Rules

### 1. Authenticated Audio Playback
- **Contract Reality**: The audio endpoint `GET /api/v1/voice/audio/{audio_id}` requires an authenticated Bearer token. Raw HTML5 `<audio src="/api/v1/voice/audio/...">` cannot attach `Authorization: Bearer <token>` headers.
- **Frontend Solution**: The frontend must use an `authenticatedAudioFetch` helper that requests the binary stream with the access token, creates an ephemeral Blob URL (`URL.createObjectURL(blob)`), and binds it to the audio element. Upon turn completion or cleanup, `URL.revokeObjectURL(url)` is invoked to prevent memory leaks.

### 2. Audio Recording Format Compatibility
- **Contract Reality**: The backend (`app/core/audio/normalizer.py`) processes uploaded files via FFmpeg, accepting WAV, OGG, or WEBM containers with Opus or PCM codecs up to 15 MB and 60 seconds duration.
- **Frontend Solution**: The frontend `useVoiceRecorder` hook will record using the standard W3C `MediaRecorder` API with mimeType `audio/webm;codecs=opus` (supported across Android Chrome, Edge, and modern browsers) with graceful fallback to `audio/ogg` or `audio/wav`.
- **User Control Invariant**: In accordance with voice interaction requirements, the UI shows visual recording status (pulsing waveform and duration counter). Recording stops and is submitted **only** upon explicit user tap on the Stop/Send button; it never auto-submits.

### 3. Token Architecture & Storage Policy
- **Contract Reality**: Access tokens expire in 15 minutes (`expires_in: 900`). Refresh tokens are single-use rotated. Token family reuse triggers immediate family-wide session invalidation.
- **Frontend Storage Rule**:
  - In-memory storage for active access token.
  - `sessionStorage` (or memory) with automatic silent background rotation at $t = \text{expires\_in} - 60s$.
  - Never store bearer or refresh tokens in insecure un-expiring `localStorage`.
  - On logout or DPDP deletion, all memory and session tokens are completely purged.

### 4. Idempotency & Optimistic Concurrency
- **Contract Reality**: The backend requires `client_turn_id` for deduplication and `expected_version` for optimistic locking in conversation turn mutations. Concurrent mutating turns or duplicate submissions return HTTP 409 (`CONVERSATION_TURN_IN_PROGRESS` or `IDEMPOTENCY_KEY_REUSED`).
- **Frontend Solution**: For each turn, the frontend generates a client turn UUID (`crypto.randomUUID()`) and includes the current conversation version. If an HTTP 409 or network timeout occurs, the UI polls `GET /api/v1/conversations/{id}` to synchronize state without corrupting the dialogue.

### 5. CORS Configuration
- **Contract Reality**: Backend `CORS_ORIGINS` defaults to `http://localhost:3000,http://127.0.0.1:3000`.
- **Adjustment**: Add `http://localhost:5173,http://127.0.0.1:5173` to `app/config.py` default settings to support standard Vite development servers without manual environment overrides.

### 6. PWA Offline-First Degradation
- **Contract Reality**: The system is offline-resilient, not offline-AI. Inference (ASR/NLU/TTS/Rules) requires network connection to the backend.
- **Frontend Solution**:
  - Service worker caches the application shell (HTML, JavaScript, CSS, PWA manifest, and Kannada Web Fonts).
  - Prominent online/offline network banner (`ಆಫ್‌ಲೈನ್‌ (Offline) - ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲ`).
  - Active conversation slots and acknowledged state are preserved in local memory.
  - Network loss during voice recording alerts the farmer and allows retry once reconnected; audio is never silently queued for background upload.
  - No authenticated API responses or farmer PII are stored in the public service worker CacheStorage.

---

## 4. UI/UX & Native Kannada Accessibility Design

1. **Native Kannada Typography**:
   - Clean, high-contrast Kannada font stack (Noto Sans Kannada / Baloo Tamma 2).
   - Dual Kannada-English bilingual labels for essential agricultural actions (e.g., `ಧ್ವನಿ ಪ್ರಾರಂಭಿಸಿ (Start Voice)`, `ಖಚಿತಪಡಿಸಿ (Confirm)`, `ಸಲಹೆಗಳು (Recommendations)`).
2. **Accessible Touch Targets**:
   - Giant primary voice microphone button ($\ge 80\text{px}$) with tactile tactile visual feedback (recording waveform, timer).
   - High color contrast ratio ($\ge 4.5:1$) compliant with WCAG 2.1 AA.
3. **Transparent Scheme Representation**:
   - Recommendations explicitly indicate status: `POTENTIALLY_MATCHED` (ಹೊಂದಾಣಿಕೆಯಾಗಬಹುದು), `INSUFFICIENT_INFORMATION` (ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ), `RULES_NOT_VERIFIED` (ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ).
   - Synthetic demonstration schemes carry unambiguous visual warnings: `[ಡೆಮೊ ಮಾತ್ರ / DEMO ONLY]`.
   - Links to official government scheme portals with clear advisory: *"ಇದು ಸರ್ಕಾರದ ಅಧಿಕೃತ ಅನುಮೋದನೆಯಲ್ಲ"* (This is not official government entitlement approval).

---

## 5. Verification Gate & Approval

This report verifies that the backend contracts are complete, consistent, and ready for frontend integration without inventing any non-existent endpoints.
