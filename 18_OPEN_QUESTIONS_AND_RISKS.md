# 18 — Open Questions, Assumptions and Risk Register

## 1. Explicit assumptions

- The first release is a hackathon prototype, not a government-authorized eligibility service.
- Kannada is the only required language for MVP.
- Website UI is owned by teammates; this repository/package covers backend AI and API contract.
- Only farmer human accounts exist; SYSTEM is an internal service identity.
- No official government API/database credentials have been supplied.
- The initial catalog has exactly five records as listed by the project owner.
- No real-scheme eligibility logic is approved by the project brief alone.
- The developer's hardware is not known; model performance is unmeasured.

## 2. Decisions needing project-owner input (not blocking M0)

1. Which mobile/account authentication method will be used for public users? Phone+password is workable for a demo but does not verify phone ownership; OTP requires provider/infrastructure.
2. Which frontend origin/domain will call the backend? Needed for final CORS/cookie configuration.
3. Does the product retain full conversation text, or only structured profile/slots and assistant response? Default recommendation: minimal structured state; transcript retention opt-in.
4. What is the target deployment host and actual CPU/RAM/GPU? Needed to select model quantization and worker concurrency.
5. Which districts/taluks and crop names must the first curated dictionary cover? Recommendation: start with pilot districts and expand through reviewed aliases.
6. Who reviews Kannada wording and model outputs? A native Kannada speaker is required for final acceptance.
7. Are demo scheme rule thresholds to be invented for simulation? If yes, project owner must approve and the UI must mark outputs DEMO ONLY.
8. Is any official state scheme dataset/API available under authorized terms? None is assumed.
9. What are the retention periods and deletion SLA for production? Set after legal review.

## 3. Risk register

| ID | Risk | Impact | Mitigation / gate |
|---|---|---|---|
| R-01 | Regional Kannada ASR errors | High | Native-speaker, accent/noise evaluation; repeat/confirm critical fields |
| R-02 | LLM hallucinates crop/location/area | Critical | Strict schema, evidence/provenance, unknown state, confirmation |
| R-03 | Incorrect scheme rules | Critical | Official-source governance, human review, versioning, rules-not-verified block |
| R-04 | Real scheme data becomes stale | High | effective dates, review_due_at, expiry policy, current notification check |
| R-05 | TTS checkpoint licence unclear | Medium/High | Verify exact checkpoint/weights terms before deployment/distribution |
| R-06 | ASR/TTS dependencies conflict | Medium | Isolated model processes/virtual environments |
| R-07 | No GPU or inadequate memory | High | Hardware inventory, quantization/CPU benchmarks, smaller worker concurrency |
| R-08 | 1,000 simultaneous inference demand | High | Queue/backpressure, staged load testing, disclose infrastructure costs |
| R-09 | Internet drop creates duplicate turns | High | Idempotency, job IDs, durable status, conversation version checks |
| R-10 | Farmer data leakage | Critical | Tenant scoping, least privilege, encryption, redacted logs, BOLA tests |
| R-11 | Raw audio retained by accident | High | Temp storage lifecycle, finally cleanup, orphan janitor, privacy tests |
| R-12 | Free hosting changes limits | Medium | Do not depend on free-tier SLA; deploy locally for demo; capacity plan |
| R-13 | Phone OTP not free | Medium | MVP password auth; OTP provider-neutral extension |
| R-14 | Unsupported benefit amount/required documents | Critical | Only source-grounded fields; omit unknown data |

## 4. Blockers that must stop implementation of affected feature

- Real scheme rules without current official source: stop recommendation activation for that scheme.
- TTS checkpoint with unclear/unsuitable terms: stop packaging/redistributing it; retain text-only output until cleared.
- No native Kannada reviewer: do not certify speech quality; mark as unvalidated.
- No hardware specification: do not select production concurrency or claim latency/SLA.
- No privacy notice/consent decision: do not collect persistent transcripts from real farmers.
