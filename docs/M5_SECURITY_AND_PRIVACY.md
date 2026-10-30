# M5 — Identity, Authorization, Privacy & Security Hardening

## 1. Overview and Core Philosophy

Milestone M5 implements production-grade farmer authentication, identity-derived authorization, secure handling of farmer data and ephemeral audio, and auditable privacy controls conforming to India's **Digital Personal Data Protection (DPDP) Act, 2023**.

### Non-Negotiable Invariants Upheld
1. **Single Human Role (`FARMER`)**: The only user-facing role is `FARMER`. No public `ADMIN` or `FACULTY` roles or privilege-escalation routes exist. Background jobs and evaluation triggers operate under internal system tokens.
2. **Identity-Derived Principal**: Farmer identity is derived strictly from a cryptographically validated JWT access token. The system never trusts `x-farmer-id`, query-parameter farmer IDs, request-body farmer IDs, or client-supplied ownership claims.
3. **Broken Object Level Authorization (BOLA) Defense**: Every farmer-owned resource enforces strict ownership at the service and database query boundary (`WHERE farmer_id = :authenticated_farmer_id`).
4. **Credential Isolation**: LLMs, ASR, and TTS services never receive database credentials or public access to farmer records.
5. **No Secret or Transcript Leakage**: Passwords, access tokens, refresh tokens, raw audio, and full farmer transcripts are never logged. Sensitive phone numbers are masked (`+91 ******1234`).
6. **Ephemeral Audio Ownership**: Ephemeral audio files are strictly owner-bound with multi-worker metadata sidecars (`{audio_id}.meta.json`). Unauthenticated or cross-farmer audio access returns 401/404.
7. **DPDP Data Rights**: Full machine-readable data export (`GET /privacy/export`) and verified data erasure with password confirmation (`POST /privacy/delete`). Immutable scheme recommendation traces are retained in an anonymized state for regulatory compliance.

---

## 2. Architecture & Subsystem Structure

```
                           +----------------------------------------+
                           |           Farmer Client                |
                           +-------------------+--------------------+
                                               |
                                     (Bearer Access Token)
                                               v
                           +----------------------------------------+
                           |       OWASP Security Headers &         |
                           |       Request Size Limiter             |
                           +-------------------+--------------------+
                                               |
                                               v
                           +----------------------------------------+
                           |  Identity Principal Derivation         |
                           |  (get_current_farmer / Token Decoder)  |
                           +-------------------+--------------------+
                                               |
                     +-------------------------+-------------------------+
                     |                         |                         |
                     v                         v                         v
     +-------------------------------+ +-------------------------------+ +-------------------------------+
     |       AuthService             | |    Conversations / Schemes    | |       PrivacyService          |
     | - Argon2id Password Hashing   | | - Identity-Derived Filtering  | | - Machine-Readable Export     |
     | - Blind Index HMAC-SHA256     | | - Strict BOLA Enforcement     | | - Verified Deletion           |
     | - Refresh Token Family Revoke | | - Recommendation Traces       | | - Ephemeral Audio Purging     |
     | - Sliding-Window Rate Limiter | | - Multi-Worker Audio Store    | | - Trace Anonymization         |
     +---------------+---------------+ +---------------+---------------+ +---------------+---------------+
                     |                                 |                                 |
                     +---------------------------------+---------------------------------+
                                                       |
                                                       v
                                    +------------------------------------+
                                    |    PostgreSQL 16 Database          |
                                    | - farmers (Argon2id, AES phone)    |
                                    | - refresh_tokens (SHA-256 hashes)  |
                                    | - conversations & turns (BOLA)     |
                                    | - recommendation_runs (Audit)      |
                                    | - audit_events & deletion_requests |
                                    +------------------------------------+
```

---

## 3. Subsystem Implementation Details

### 3.1 Farmer Authentication & Credential Storage (`app/services/auth_service.py`, `app/core/security/`)
- **Phone Number Normalization & Blind Indexing**: Indian mobile numbers are normalized to E.164 (`+91XXXXXXXXXX`). Plaintext phone numbers are never stored in indexable columns; an HMAC-SHA256 blind index (`phone_number_hash`) allows deterministic duplicate detection and login lookups, while the actual phone number is encrypted at rest using AES-256-GCM (`phone_number_encrypted`).
- **Argon2id Password Hashing**: Passwords are hashed using Argon2id with 64 MB memory cost, 3 iterations, and 4 parallel threads (`app/core/security/password.py`), providing resistance against GPU/ASIC cracking.
- **Timing Attack Mitigation**: When login fails on non-existent accounts, a constant-time dummy password verification is executed (`dummy_verify_password`) ensuring response duration parity.
- **Generic 401 Error Invariants**: Failed login on existing or non-existent accounts returns identical generic responses: `"Invalid phone number or password"` with code `UNAUTHORIZED`, preventing username enumeration.
- **Brute-Force Rate Limiting & Account Lockout**:
  - Sliding-window in-memory rate limiter (`RateLimiter`) throttles registration to 5 attempts / 15 minutes and login attempts.
  - Adaptive account lockout locks an account for 15 minutes after 5 consecutive failed login attempts (`account_status = 'LOCKED'`). Lockouts auto-unlock upon expiration.

### 3.2 Token Architecture & Family Reuse Detection (`app/core/security/jwt.py`, `app/models/auth.py`)
- **Short-Lived Access Tokens**: Signed JWT with HS256, 15-minute expiration, containing `sub: farmer_id`, `type: access`, `iat`, and `exp`.
- **Rotated Refresh Tokens**: Cryptographically secure 256-bit random tokens (`secrets.token_urlsafe(32)`). Plaintext tokens are **never** stored in the database; only SHA-256 hashes are persisted in `refresh_tokens`.
- **Token Family Rotation & Reuse Revocation**:
  - Each refresh token belongs to a `family_id` (UUID).
  - On rotation, the current token is revoked and assigned `replaced_by_id`.
  - If an already-revoked refresh token is presented (indicating token theft or replay), the system immediately detects reuse, revokes the **entire token family**, logs a `TOKEN_REUSE_DETECTED` audit event, and invalidates all active sessions.

### 3.3 Identity-Derived Authorization & BOLA Defense (`app/core/security/auth.py`)
- **Dependencies**: `get_current_farmer` and `get_current_farmer_id` extract the Bearer token, validate signature and claims, check farmer account status (`ACTIVE` vs `LOCKED`/`DELETED`), and return the authenticated principal.
- **Route Authorization Audit**:
  - `POST /api/v1/conversations/` -> `get_current_farmer_id`
  - `GET /api/v1/conversations/active` -> `get_current_farmer_id`
  - `GET /api/v1/conversations/{id}` -> `WHERE id = :id AND farmer_id = :authenticated_id`
  - `POST /api/v1/conversations/{id}/turns` -> `get_current_farmer_id`
  - `POST /api/v1/schemes/evaluate` -> `get_current_farmer`
  - `GET /api/v1/schemes/runs/{run_id}` -> `WHERE id = :run_id AND farmer_id = :authenticated_id`
  - `POST /api/v1/voice/turn` -> `get_current_farmer`
  - `GET /api/v1/voice/audio/{audio_id}` -> `get_current_farmer`
  - `GET /api/v1/privacy/export` -> `get_current_farmer`
  - `POST /api/v1/privacy/delete` -> `get_current_farmer`
- All legacy `x-farmer-id` header dependencies were completely eliminated. Supplying a spoofed `x-farmer-id` header has zero effect on data access.

### 3.4 Hardened Ephemeral Audio Store (`app/core/tts/storage.py`)
- **Owner-Binding Invariant**: Audio files synthesized by TTS store the owner's farmer ID in an adjacent filesystem sidecar (`{audio_id}.meta.json`). Audio retrieval strictly checks `expected_owner == authenticated_farmer_id`. Attempts by unauthenticated callers or other farmers to access audio return 401/404.
- **Multi-Worker Safety**: Persisting sidecar metadata directly to disk guarantees consistent owner checks across multi-process Uvicorn deployments sharing a filesystem.
- **Path Traversal Defense**: Audio IDs are validated as strictly alphanumeric; attempts to pass `../` are rejected.
- **Automated TTL Purging**: Files older than TTL (default 10 minutes) and their sidecars are purged automatically.

### 3.5 DPDP Act 2023 Data Portability and Verified Erasure (`app/services/privacy_service.py`)
- **Data Portability (`GET /api/v1/privacy/export`)**: Returns a structured, machine-readable JSON document containing profile data, consent history, conversation sessions, turn transcripts, slots, and scheme evaluation traces. Passwords, hashes, and encryption keys are strictly omitted.
- **Verified Erasure (`POST /api/v1/privacy/delete`)**:
  - Re-authenticates farmer with password confirmation before initiating deletion.
  - Purges all farmer response audio files from the ephemeral audio store.
  - Deletes conversation sessions, turns, and slot values.
  - Deletes farmer profile records and active refresh tokens.
  - Withdraws all consent records.
  - Anonymizes immutable recommendation runs: statutory audit traces are retained, but profile snapshots are redacted (`{"redacted": True, "reason": "DPDP_ERASURE_REQUEST"}`).
  - Deactivates farmer account (`account_status = 'DELETED'`, phone number scrambled, password set to `'DELETED'`).
  - Records an immutable `ACCOUNT_DELETED` audit event without personal identifiers.

### 3.6 Security Hardening (`app/main.py`, `app/config.py`)
- **OWASP Security Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Content-Security-Policy: default-src 'self'`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Request Size Limiting**: Rejects requests exceeding 15 MB for multipart audio uploads and 2 MB for JSON bodies with HTTP 413.
- **Environment Secret Key Validation**: Enforces strong secrets in production environments.

---

## 4. Test Suite and Verification

The test suite contains **201 automated tests** covering all security, identity, authorization, BOLA, audio, and privacy workflows.

| Test File | Category | Focus |
|-----------|----------|-------|
| `tests/unit/test_security_password.py` | Unit | Argon2id hashing, salt uniqueness, constant-time dummy verify |
| `tests/unit/test_security_crypto.py` | Unit | E.164 phone normalization, HMAC-SHA256 blind indexing, AES-256-GCM encryption |
| `tests/unit/test_security_jwt.py` | Unit | Access token signing, claims verification, expiration, refresh token pair generation |
| `tests/unit/test_security_rate_limiter.py` | Unit | Sliding-window attempt counting, window expiry, thread-safe locks |
| `tests/unit/test_security_audio_store.py` | Unit | Owner binding, sidecar persistence, multi-worker safety, traversal defense |
| `tests/unit/test_security_services.py` | Unit | Edge cases in `AuthService`, `PrivacyService`, and `get_current_farmer` dependencies |
| `tests/integration/test_auth_endpoints.py` | Integration | Registration, login enumeration prevention, refresh token rotation, family reuse revocation, logout, lockout |
| `tests/integration/test_authorization_bola.py` | Integration | Unauthenticated rejection across all routes, BOLA cross-farmer isolation, header spoofing resistance |
| `tests/integration/test_privacy_lifecycle.py` | Integration | Machine-readable export, password-verified erasure, audio store purging, token invalidation |

**Total Suite Result**: `201 passed in 27.11s`  
**Total Statement Coverage**: **90%** (3,591 covered / 3,971 statements)
