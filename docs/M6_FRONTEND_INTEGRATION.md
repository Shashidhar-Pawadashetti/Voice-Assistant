# M6 — Farmer Frontend Integration & Offline-First Experience

## 1. Executive Summary

Milestone M6 delivers the complete farmer-facing Progressive Web App (PWA) for Krishi Mitra, integrating the frontend with the existing M0–M5 FastAPI backend.

The frontend is a modern, responsive, installable application built in `frontend/` using React 18, TypeScript, and Vite. It is designed specifically for rural farmers with low digital literacy, featuring native Kannada typography, high-contrast accessible visual cues, large touch controls, voice-first interaction with explicit user submission, offline status detection, and DPDP Act 2023 privacy controls.

---

## 2. Architecture & Design Principles

```
                             +----------------------------------------+
                             |           Browser / PWA                |
                             |  - Installable Web App Manifest        |
                             |  - Service Worker Shell Cache          |
                             |  - Network Status Beacon (Online/Off)  |
                             +-------------------+--------------------+
                                                 |
                                                 v
                             +----------------------------------------+
                             |        Farmer View Layer (React)       |
                             |  - Native Kannada Typography           |
                             |  - Dual Kannada/English Labels         |
                             |  - Giant Voice Mic Button (>= 80px)    |
                             |  - Tactile Waveform & Recording Timer  |
                             |  - Assistant Speech Audio Player       |
                             |  - Agricultural Fact Confirmation Box  |
                             |  - Scheme Cards (DEMO_ONLY Ribbon)     |
                             +-------------------+--------------------+
                                                 |
                                                 v
                             +----------------------------------------+
                             |      State & Services Layer            |
                             |  - In-Memory Access Token Storage      |
                             |  - Silent Refresh Rotation             |
                             |  - Idempotent Turns (client_turn_id)   |
                             |  - Authenticated Audio Blob Fetcher    |
                             |  - Zero Cache on Authenticated APIs    |
                             +-------------------+--------------------+
                                                 |
                                     (HTTPS / JSON & Multipart)
                                                 v
                             +----------------------------------------+
                             |      Krishi Mitra Backend (M0-M5)      |
                             |  - Fast, Deterministic 3-Valued Rules  |
                             |  - ASR / NLU / TTS Orchestration       |
                             |  - DPDP Data Portability & Erasure     |
                             +----------------------------------------+
```

### Non-Negotiable Invariants Upheld

1. **Explicit User Submission (Never Auto-Submit)**:
   - In accordance with voice interaction requirements, the voice recording interface displays live duration and a visual pulse. Recording finishes and submits to the backend **only** when the farmer explicitly taps the "Stop & Submit" button. The user can also cancel without submitting.
2. **Authenticated Audio Retrieval**:
   - The backend audio endpoint `GET /api/v1/voice/audio/{audio_id}` enforces strict owner-binding. The frontend fetches audio via an authenticated `fetch` with `Authorization: Bearer <token>`, converts the response to a temporary local Blob URL (`URL.createObjectURL(blob)`), and revokes the URL on unmount.
3. **Zero Cache on Personal Data**:
   - The PWA Service Worker (`public/sw.js`) strictly caches only the application shell (HTML, CSS, JS, manifest, and icons). It explicitly bypasses caching for any route matching `/api/*` or `/health/*`. No personal data or authenticated responses are stored in public cache storage.
4. **Offline Resilience**:
   - When the user loses network connectivity, a persistent red banner informs them in Kannada: *"ಆಫ್‌ಲೈನ್‌ (Offline) — ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲ"*. Voice recording is disabled while offline with instructions to reconnect, avoiding silent failures or lost speech data.
5. **Strict DEMO_ONLY Scheme Warning**:
   - Synthetic demonstration schemes carry prominent, unmistakable warning banners (`[ಡೆಮೊ ಮಾದರಿ ಮಾತ್ರ / DEMO ONLY]`), clearly differentiating them from real schemes like PM-KISAN.
6. **Statutory Non-Entitlement Disclaimers**:
   - Recommendation headers and scheme cards clearly state in native Kannada: *"ಇದು ಸರ್ಕಾರದ ಅಂತಿಮ ಮಂಜೂರಾತಿ ಅಲ್ಲ. ಅಂತಿಮ ನಿರ್ಧಾರ ಸಂಬಂಧಪಟ್ಟ ಇಲಾಖೆಯದ್ದಾಗಿದೆ."*

---

## 3. Component Hierarchy & User Journeys

### 3.1 Authentication & Session Lifecycle (`frontend/src/pages/LoginPage.tsx`, `RegisterPage.tsx`)
- Mobile number validation (10 digits) with phone number masking upon authentication.
- Argon2id password authentication with timing-attack and brute-force mitigation handling.
- Session restoration via `sessionStorage` refresh token check on page reload.
- Automatic logout clears all memory and session credentials.

### 3.2 Conversational Voice & Text Interface (`frontend/src/pages/ConversationPage.tsx`)
- Multi-turn conversation view with message bubbles (`TurnBubble.tsx`).
- Voice turn submission via `VoiceMicButton.tsx` (using W3C `MediaRecorder` with `audio/webm;codecs=opus`).
- Text turn fallback for noisy environments or blocked microphones.
- Dialogue state machine badge (`GREETING`, `COLLECTING_SLOTS`, `CONFIRMING`, `EVALUATION_READY`, `COMPLETED`).
- Extracted slot facts drawer (`SlotFactList.tsx`) displaying current agricultural attributes (district, taluk, crop, land size, irrigation source) with confirmation tags.
- Direct "Check Scheme Eligibility" action button once `EVALUATION_READY` is reached.

### 3.3 Scheme Discovery & Recommendations (`frontend/src/pages/SchemesPage.tsx`, `SchemeCard.tsx`)
- Status badges:
  - `POTENTIALLY_MATCHED`: Green (`ಹೊಂದಾಣಿಕೆಯಾಗಬಹುದು`)
  - `INSUFFICIENT_INFORMATION`: Amber (`ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ`)
  - `VERIFICATION_REQUIRED`: Blue (`ದಾಖಲೆ ಪರಿಶೀಲನೆ ಬಾಕಿ`)
  - `RULES_NOT_VERIFIED`: Grey (`ಅಧಿಕೃತ ಪರಿಶೀಲನೆ ಬಾಕಿ`)
  - `NOT_MATCHED`: Red (`ಅರ್ಹತೆ ಹೊಂದಿಲ್ಲ`)
- Expandable explanation traces showing matched, failed, and unverified conditions.
- Deep links to official government portals (`pmkisan.gov.in`, `pmfby.gov.in`).

### 3.4 Data Rights & Privacy (`frontend/src/pages/SettingsPrivacyPage.tsx`)
- DPDP Act 2023 compliance:
  - **Data Export Modal**: Downloads a structured machine-readable JSON file with complete profile data, conversation history, and recommendation traces.
  - **Account Deletion Modal**: Requires password confirmation to trigger verified erasure of all personal data, conversational history, audio files, and credentials.

---

## 4. Verification & Testing

### Frontend Automated Test Suite
- `tests/i18n.test.ts`: Verifies complete native Kannada string dictionary, dialogue state mappings, and statutory disclaimers.
- `tests/api_auth.test.ts`: Verifies secure in-memory and `sessionStorage` token isolation, Bearer header injection, and logout purging.
- `tests/pwa.test.ts`: Verifies PWA `manifest.json` standalone configuration and `sw.js` invariant enforcing zero caching on `/api/*`.
- `tests/scheme_card.test.ts`: Verifies synthetic `DEMO_ONLY` flags, official verification requirements, and status badges.

**Test Run Output:**
```text
> krishi-mitra-frontend@1.0.0 test
> node --experimental-strip-types --test tests/i18n.test.ts tests/api_auth.test.ts tests/pwa.test.ts tests/scheme_card.test.ts

✔ Tokens are managed in memory and sessionStorage safely (1.04ms)
✔ Kannada localization contains all required top-level sections (0.82ms)
✔ Kannada scheme statuses match backend RecommendationStatus enums (0.14ms)
✔ Kannada dialogue states match backend DialogueState enums (0.15ms)
✔ PWA manifest.json has valid standalone configuration and Kannada name (1.24ms)
✔ Service Worker sw.js strictly enforces zero caching on authenticated API routes (0.73ms)
✔ Scheme recommendation model handles DEMO_ONLY and status variants correctly (0.71ms)
ℹ tests 7
ℹ pass 7
ℹ fail 0
```

### Production Build Verification
```text
> krishi-mitra-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
✓ 1601 modules transformed.
dist/index.html                   1.75 kB │ gzip:  0.91 kB
dist/assets/index-BBBk5kTS.css    1.62 kB │ gzip:  0.78 kB
dist/assets/index-CYYUQry5.js   212.72 kB │ gzip: 64.51 kB │ map: 556.02 kB
✓ built in 1.61s
```

### Backend Test Suite
All **201 backend integration and unit tests** continue to pass cleanly in `26.77s` with zero regressions.
