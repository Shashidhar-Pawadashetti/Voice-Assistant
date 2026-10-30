# 02 — Product Requirements Specification

## 1. Functional requirements

### FR-001 — Farmer authentication

The backend shall authenticate farmer accounts. Every farmer-owned resource must be scoped to the authenticated farmer. The MVP may use a secure account identifier and password flow; phone OTP delivery is a later integration because it needs an SMS provider and is not assumed free.

### FR-002 — Start and resume conversations

A farmer can create a conversation, continue an active one and retrieve prior saved conversations. Conversation retrieval must never disclose another farmer's data.

### FR-003 — Kannada audio input

The backend accepts a bounded audio upload from the frontend. It validates file type, size, duration and decodability; normalizes audio for the configured ASR model; and produces a Kannada transcript or a clear recoverable error.

### FR-004 — Text input fallback

A farmer can submit text when microphone permissions, audio hardware or connectivity make voice input unavailable. Text input is a fallback; the primary experience remains voice-first.

### FR-005 — Natural-language interpretation

The NLU layer shall extract intent and agricultural slots into a strict schema. It must preserve uncertainty and not invent missing values. All outputs must pass schema validation before being used.

### FR-006 — Vocabulary normalization

The system shall map common Kannada terms, local synonyms and code-mixed phrases to canonical entities while retaining the original utterance/transcript only according to retention consent. Examples include crop aliases, district/taluk names, irrigation types, seasons and area units.

### FR-007 — Unit normalization

Land units must be converted using explicit, tested conversion rules. Baseline constants: 1 acre = 0.40468564224 hectares; 1 acre = 40 guntas; 1 gunta = 1/40 acre. Keep original value/unit alongside normalized values. Ask for clarification if the utterance is ambiguous.

### FR-008 — Progressive slot filling

The dialogue manager identifies the next missing field required for the current intent/scheme path. It asks one focused question at a time and avoids asking unrelated fields.

### FR-009 — Confirmation and correction

The assistant must read back critical extracted values (district, crop, area, season, ownership) and allow correction. A correction updates the current slot rather than creating an independent conflicting fact. The system records the change in a minimal audit trail.

### FR-010 — Conversation context

Context persists across turns and can be resumed. The system retrieves only the active structured profile/slots, short summary and limited recent turns necessary for the next response.

### FR-011 — Scheme recommendation

The scheme engine evaluates structured farmer facts against versioned deterministic rules. The LLM must not execute eligibility decisions or modify outcomes.

### FR-012 — Explainable outcomes

Each evaluation returns rule version, evaluated timestamp, matched conditions, failed conditions, unknown conditions, source references and a cautious outcome. Fictional schemes are visibly separated from real schemes.

### FR-013 — Kannada response and TTS

The assistant generates concise Kannada responses, then TTS produces audio. If TTS fails, return the text response and a speech-unavailable indicator; do not fail the entire conversational turn.

### FR-014 — Privacy controls

Raw farmer audio is processed transiently and not persisted by default. Data collection requires an appropriate notice and affirmative consent for the stated purposes. A farmer can request deletion of their saved data.

### FR-015 — Job recovery

Long-running voice processing must expose request/job IDs and stable statuses so the frontend can safely retry/poll after network loss without duplicating a turn.

### FR-016 — Scheme freshness

Every real scheme definition includes source URLs, effective/verification date, rule version and verification state. Expired, missing or unverified scheme information must be disclosed and cannot produce a confident recommendation.

## 2. NLU intent taxonomy (initial)

- `GREETING`
- `HELP`
- `FIND_SCHEMES`
- `INCOME_SUPPORT`
- `CROP_INSURANCE`
- `MICRO_IRRIGATION`
- `AGRICULTURAL_EQUIPMENT`
- `SOIL_IMPROVEMENT`
- `PROFILE_UPDATE`
- `CORRECT_PREVIOUS_ANSWER`
- `REPEAT_LAST_RESPONSE`
- `EXPLAIN_SCHEME`
- `APPLICATION_STEPS`
- `UNKNOWN`

Intent taxonomy may be expanded by an ADR-backed change; unknown input must always have a safe fallback.

## 3. Initial agricultural slot catalogue

| Slot | Canonical shape | Required when | Confirmation |
|---|---|---|---|
| state | ISO-like canonical state code/name | All real scheme discovery | Confirm if inferred |
| district | canonical district ID/name | Most scheme discovery | Yes |
| taluk | canonical taluk ID/name | When scheme/notified-area specificity requires | Yes |
| village | canonical name/code | Only when necessary | Yes |
| land_area | numeric + original unit + acres/hectares | Landholding/land-area rule | Yes |
| land_ownership | `OWNER`, `TENANT`, `SHARECROPPER`, `OTHER`, `UNKNOWN` | Scheme-dependent | Yes; never infer from land area |
| crop | canonical crop code/name | Crop-related schemes | Yes |
| season | `KHARIF`, `RABI`, `SUMMER`, `OTHER`, `UNKNOWN` | Seasonal insurance/notification | Yes |
| irrigation_type | `RAINFED`, `BOREWELL`, `CANAL`, `DRIP`, `SPRINKLER`, `OTHER`, `UNKNOWN` | Irrigation schemes | Yes |
| assistance_need | controlled enum | Initial discovery | Confirm if unclear |
| land_record_status | `SELF_REPORTED`, `DOCUMENT_VERIFIED`, `GOVT_VERIFIED`, `UNKNOWN` | Only if required | Must not claim verified without evidence |
| ekyc_status | `DONE`, `PENDING`, `UNKNOWN` | Where official rule requires | User-reported, not government verified |

Do not ask all slots for every farmer. The scheme rule set declares required slots.

## 4. Non-functional requirements

### NFR-001 — Correctness

Never turn missing facts into positive eligibility. Unknown must remain unknown until confirmed by an allowed evidence source.

### NFR-002 — Explainability

All scheme results must be reproducible from the stored profile facts and the exact immutable rule version.

### NFR-003 — Security

TLS in transit, secure password hashing, token protection, authorization checks on every farmer resource, restricted model/worker network access, secret management and non-sensitive logs.

### NFR-004 — Privacy

No raw audio persistence by default; data minimization; purpose-specific consent; retention controls; deletion workflow; no third-party AI transfer in MVP.

### NFR-005 — Reliability

A failed ASR/LLM/TTS worker must result in an explicit error or degraded response, not a fabricated answer. Requests must be idempotent.

### NFR-006 — Maintainability

ASR, LLM and TTS behind interfaces; scheme rules data-driven and versioned; API versioned; code modular but initially deployed as a modular monolith plus separate model processes where necessary.

### NFR-007 — Performance

Measure each pipeline stage separately. Set full-turn latency targets only after establishing a baseline on documented hardware. Non-inference API operations should be kept responsive and not share model-worker execution pools.

### NFR-008 — Accessibility

Plain Kannada language, short spoken responses, text transcript option, replay option and clear network/microphone errors.

### NFR-009 — Scalability

Stateless API processes, bounded queues, configurable worker concurrency, connection pooling, rate limiting and metrics. No claim of 1,000 concurrent voice inference until tested.

### NFR-010 — License compliance

Record code, model and checkpoint licences separately. Do not assume the repository's code licence automatically applies to downloaded weights, datasets or third-party dependencies.

## 5. Out-of-scope safeguards

- Do not make a legal/financial promise.
- Do not submit applications or modify government records.
- Do not infer a farmer's caste, religion, income, gender or other sensitive attributes unless a future verified scheme requirement and explicit lawful basis make it necessary; this is not in MVP.
- Do not collect voiceprints or use voice as identity authentication.
