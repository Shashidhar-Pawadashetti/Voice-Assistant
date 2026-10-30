# 14 — Test Strategy and Evaluation Plan

## 1. Test layers

- unit: pure parsing, unit conversion, slot merge, state transitions, rule operators;
- adapter tests: mock Ollama/ASR/TTS responses and failure modes;
- integration: PostgreSQL, auth, ownership, job state, file cleanup;
- end-to-end: audio/text -> transcript -> NLU -> dialogue -> scheme rules -> Kannada response/TTS;
- security: authentication, BOLA/IDOR, rate limits, upload abuse, secret/log scanning;
- privacy: audio deletion, transcript consent, deletion request, log redaction;
- performance: stage timing and Locust concurrency tests;
- human evaluation: native Kannada speakers assess intelligibility and correctness.

## 2. Kannada evaluation corpus

Build a small initial, consented evaluation set (target 50–100 utterances for first baseline; expand as possible). It must include held-out speakers and should cover:

- Northern Karnataka / Dharwad-Belagavi-Hubballi region speech patterns;
- southern/central Kannada examples;
- different ages/genders only where voluntarily contributed and handled respectfully;
- different speaking speeds;
- outdoor/agricultural background noise;
- Kannada-English code-mixing;
- crop names and local aliases;
- district/taluk/village names;
- land numbers and fractions;
- corrections and negation;
- questions about PM-KISAN / PMFBY and synthetic categories.

Record consent and purpose. Do not collect recordings from farmers without explicit informed consent. Keep raw evaluation audio in a restricted, separately consented dataset with deletion controls; it is not production audio retention.

## 3. ASR metrics

- WER (Word Error Rate);
- CER (Character Error Rate);
- exact-match rate for high-impact terms: crop, district, land area, season, negation;
- accuracy grouped by accent/noise/code-mix conditions.

Human-reviewed transcript is the reference. A low aggregate WER can hide an unacceptable error on numeric land area or crop name; report critical slot accuracy separately.

## 4. NLU / dialogue metrics

- intent accuracy and macro F1;
- slot-level precision/recall/F1;
- exact match for numeric area/unit and canonical crop/location;
- correction resolution accuracy;
- number of redundant follow-up questions;
- proportion of missing facts incorrectly filled;
- conversation completion rate;
- native-speaker rating for question clarity.

Any fabricated critical value is a release-blocking defect.

## 5. Scheme engine tests

For each rule:

- TRUE case;
- FALSE case;
- UNKNOWN case;
- boundary case;
- stale/effective-date case;
- hard exclusion case;
- conflicting fact case;
- synthetic-vs-real classification case.

Test determinism: same profile snapshot + same rule hash + evaluator version must produce identical outcome/trace.

Test that every real `INCOMPLETE`/`EXPIRED` scheme produces `RULES_NOT_VERIFIED`, never a positive result.

Test that every synthetic output has `demo_only=true` and prominent demo label.

## 6. Privacy/security tests

- input audio is deleted after successful ASR;
- input audio is deleted after ASR failure/timeout/cancellation;
- orphan cleanup removes abandoned temp files;
- transcript is not stored when consent is absent or withdrawn;
- log capture contains no audio/transcript/token/password/phone;
- farmer A cannot retrieve farmer B conversation, job, recommendation, profile or audio response;
  *(Verified in Milestone M3 via `test_farmer_ownership_isolation`).*
- invalid/expired tokens denied;
- refresh token rotation/revocation works;
- deletion removes linked data/cache/audio and prevents job resurrection;
- malicious audio and malformed media are rejected safely.

## 7. Reliability tests

Simulate:

- API restart after job acceptance;
- worker crash during ASR/LLM/TTS;
- queue unavailable;
- DB unavailable;
- model server timeout;
- duplicate request retry;
- same idempotency key with different payload;
- network loss before upload, during processing and after result generation;
- concurrent turns in one conversation.

## 8. Performance/load testing

Use Locust for HTTP/API workload; audio fixtures should be bounded and synthetic/consented. Separate tests for 1,000 open sessions from simultaneous audio inference jobs.

Ramp: 10 -> 25 -> 50 -> 100 -> 250 -> 500 -> 1,000 sessions as hardware permits. For model jobs, ramp separately and record queue time, worker utilization, failure and p95 latency. Stop when resource limits or SLO thresholds are breached.

Do not publish a concurrency number without the machine specification, software/model versions, quantization, request mix and measured results.

## 9. Initial release gates

- No critical-value hallucination in the evaluation set.
- All API ownership tests pass.
- All real unverified schemes remain blocked from positive recommendation.
- No raw audio retained in normal processing path.
- Audio cleanup tests pass for success and failure.
- LLM schema failures are handled safely.
- End-to-end voice and text fallback both work.
- Native Kannada reviewers approve core voice prompts and TTS intelligibility for demo use.
- Performance results are documented; no unsupported 1,000-user claim.

> [!NOTE]
> **Milestone M4 Test Deliverables:**
> - Unit tests for 3-valued logic truth tables, all operators, effective dates, exclusions in `tests/unit/test_scheme_evaluator.py`.
> - Repository, explainability and BOLA tests in `tests/unit/test_recommendation_service.py`.
> - End-to-end scheme recommendation integration tests in `tests/integration/test_scheme_recommendation.py`.
> - M3 dialogue and automatic scheme evaluation tests in `tests/integration/test_dialogue_scheme_integration.py`.
>
> **Milestone M5 Test Deliverables:**
> - Unit tests for Argon2id hashing, salt uniqueness, and timing mitigation in `tests/unit/test_security_password.py`.
> - Unit tests for E.164 phone normalization, HMAC-SHA256 blind indexing, and AES-256-GCM encryption in `tests/unit/test_security_crypto.py`.
> - Unit tests for JWT access token signing, decoding, expiration, and refresh token pair generation in `tests/unit/test_security_jwt.py`.
> - Unit tests for sliding-window rate limiting in `tests/unit/test_security_rate_limiter.py`.
> - Unit tests for audio store owner binding, multi-worker metadata sidecars, and path traversal defense in `tests/unit/test_security_audio_store.py`.
> - Unit tests for `AuthService`, `PrivacyService`, and `get_current_farmer` dependency edge cases in `tests/unit/test_security_services.py`.
> - Integration tests for registration, login enumeration prevention, refresh token rotation, family reuse revocation, logout, and lockout in `tests/integration/test_auth_endpoints.py`.
> - Integration tests for BOLA defense, cross-farmer isolation, header spoofing rejection, and audio access control in `tests/integration/test_authorization_bola.py`.
> - Integration tests for DPDP data export and password-verified erasure workflows in `tests/integration/test_privacy_lifecycle.py`.
> - Full test suite: **201 passed**, **90% statement coverage**.

Exact percentage thresholds for WER, intent accuracy and slot extraction must be set after the first baseline and reviewed with native Kannada speakers; do not fabricate a quality number in advance.
