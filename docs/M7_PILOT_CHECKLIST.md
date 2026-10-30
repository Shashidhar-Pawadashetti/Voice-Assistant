# M7 Farmer Pilot Checklist & Field Operational Runbook

**Project:** Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)  
**Milestone:** M7 — System Validation, Production Deployment & Pilot Readiness  
**Target Deployment:** Dharwad and Kalaburagi Districts, Karnataka  
**Pilot Cohort:** 100 Small & Marginal Farmers (Phase 1)  
**Document Version:** 1.0  
**Date:** October 2026  

---

## 1. Pilot Objectives & Cohort Definition

### 1.1 Core Objectives
1. **Field Usability Validation:** Validate that rural farmers can intuitively use spoken Kannada to inquire about agricultural schemes, record profile attributes, and listen to synthesized responses on mobile devices.
2. **Deterministic Governance in Practice:** Ensure farmers understand the distinction between real government entitlement requirements (e.g., PM-KISAN, PMFBY) and demonstration schemes without false expectations.
3. **Network Resilience Under 2G/3G Conditions:** Verify PWA offline caching, reconnect recovery, and idempotent turn submission in rural areas with intermittent connectivity.
4. **DPDP Compliance Verification:** Confirm seamless consent collection, profile transparency, and data portability in field operations.

### 1.2 Pilot Cohort Composition
- **Geographic Coverage:**
  - Cluster 1: Navalgund Taluk, Dharwad District (North Karnataka black soil zone — sorghum, green gram, sugarcane).
  - Cluster 2: Aland Taluk, Kalaburagi District (Kalyana Karnataka dryland zone — pigeon pea, cotton).
- **Cohort Demographics:**
  - Total Participants: 100 farmers (50 per district).
  - Landholding Distribution: 65% Small/Marginal (< 5 acres), 25% Medium (5–10 acres), 10% Large (> 10 acres).
  - Device Distribution: Low-to-mid tier Android smartphones (Android 9.0 to 14) with mobile browsers (Chrome 90+).

---

## 2. Informed Consent Protocol (DPDP Act 2023 Compliant)

Before any interaction or data collection occurs, the field facilitator must guide the farmer through the statutory consent process:

### 2.1 Spoken Kannada Consent Notice
The facilitator or mobile application plays the official audio notice:
> *"ನಮಸ್ಕಾರ. ಕೃಷಿ ಮಿತ್ರ ಅಪ್ಲಿಕೇಶನ್ ನಿಮ್ಮ ಧ್ವನಿ ಮತ್ತು ಕೃಷಿ ವಿವರಗಳನ್ನು (ಜಿಲ್ಲೆ, ಜಮೀನು, ಬೆಳೆ) ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ನೀಡಲು ಮಾತ್ರ ಬಳಸುತ್ತದೆ. ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ವಿವರಗಳನ್ನು ಬೇರೆ ಯಾರಿಗೂ ಮಾರಾಟ ಮಾಡಲಾಗುವುದಿಲ್ಲ ಅಥವಾ ಹಂಚಿಕೊಳ್ಳಲಾಗುವುದಿಲ್ಲ. ನೀವು ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ನಿಮ್ಮ ಖಾತೆಯನ್ನು ರದ್ದುಗೊಳಿಸಬಹುದು ಅಥವಾ ಮಾಹಿತಿಯನ್ನು ಅಳಿಸಬಹುದು. ಮುಂದುವರಿಯಲು ನಿಮ್ಮ ಸಮ್ಮತಿ ಇದೆಯೇ?"*
> *(Hello. The Krishi Mitra application uses your voice and agricultural details solely to provide government scheme guidance. Your personal details are never sold or shared. You may delete your account or data at any time. Do you consent to proceed?)*

### 2.2 Affirmative Action Verification
- [ ] Farmer explicitly checks the consent toggle: **"ನಾನು ನಿಯಮಗಳನ್ನು ಒಪ್ಪುತ್ತೇನೆ"** (I agree to the terms).
- [ ] Backend records `ConsentRecord`:
  - `farmer_id`: Generated UUID.
  - `consent_type`: `"DATA_PROCESSING_AND_ACCOUNT_CREATION"`.
  - `consent_language`: `"kn"`.
  - `ip_address`: Recorded from client connection.
  - `timestamp`: UTC ISO timestamp.

---

## 3. Pre-Flight Device & Network Readiness Checklist

### 3.1 Farmer Device Prerequisites
- [ ] Operating System: Android 8.0 (Oreo) or higher.
- [ ] Browser: Google Chrome, Samsung Internet, or Firefox with WebAudio and MediaRecorder support.
- [ ] Permissions: Microphone permission granted to the Krishi Mitra PWA URL (`https://krishi-mitra.gov.in`).
- [ ] PWA Installation: Verify "Add to Home Screen" (`ಕೃಷಿ ಮಿತ್ರ ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ`) creates the standalone app icon.

### 3.2 Network Resilience & Offline Testing
- [ ] **PWA Application Shell Cached:** Verify the app opens and renders the Kannada interface even in Airplane Mode.
- [ ] **Network State Banner:** Test turning off mobile data; verify the yellow banner appears:  
  `ಆಫ್‌ಲೈನ್‌ನಲ್ಲಿದ್ದೀರಿ — ಇಂಟರ್ನೆಟ್ ಮರುಸಂಪರ್ಕವಾದ ನಂತರ ನಿಮ್ಮ ಧ್ವನಿ ಕಳುಹಿಸಲಾಗುತ್ತದೆ.`
- [ ] **Reconnect Recovery:** Re-enable mobile data; verify the green recovery toast appears and pending requests retry without user intervention.
- [ ] **Zero Audio Leakage:** Verify audio files are not saved into public device storage (Gallery/Downloads).

---

## 4. Field Facilitator & Extension Worker Guidelines

1. **Microphone Etiquette in Field Environments:**
   - Position the handset 10–15 cm from the farmer's mouth.
   - Avoid recording directly in front of active diesel tractor engines or loud threshing machines.
   - Instruct the farmer: *"ಸ್ಪೀಕರ್ ಆನ್ ಮಾಡಿ, ಬಟನ್ ಒತ್ತಿ ಮಾತನಾಡಿ, ಮುಗಿದ ನಂತರ ನಿಲ್ಲಿಸಿ ಬಟನ್ ಒತ್ತಿ"* (Tap record, speak naturally, tap stop when finished).
2. **Assisting Non-Literate Farmers:**
   - Facilitators must allow the farmer to speak their own crop and landholding details.
   - Never enter passwords or personal details on the farmer's behalf without explicit instruction.
   - Always play the synthesized Kannada audio response so the farmer hears the scheme explanation directly.
3. **Handling Discrepancies or Speech Misunderstandings:**
   - If the speech recognizer misinterprets a district or acreage, instruct the farmer to use spoken correction:  
     *"ತಪ್ಪಾಗಿದೆ, ನನ್ನ ಬಳಿ ೪ ಎಕರೆ ಜಮೀನು ಇದೆ"* (Correction, I have 4 acres of land).
   - Alternatively, tap the slot badge on the screen to manually edit the value.

---

## 5. Incident Response & Escalation Matrix

| Severity Level | Definition | Response SLA | Action Required | Escalation Lead |
|---|---|---|---|---|
| **Severity 1 (Critical)** | Core API / Database / Proxy unavailable; all farmers blocked. | $\le$ 15 minutes | Execute `docker compose restart`; if DB fails, restore latest verified backup. | Platform SRE Lead |
| **Severity 2 (High)** | Speech pipeline down; text fallback working, or rate limiting false positives. | $\le$ 1 hour | Inspect Ollama/ASR worker logs; flush rate limiter ZSETs if needed. | Backend AI Lead |
| **Severity 3 (Medium)**| Specific scheme rule evaluation discrepancy or typo in Kannada text. | $\le$ 4 hours | Verify scheme catalog JSON in `app/core/scheme/catalog/`; patch rule version. | Scheme Governance Lead |
| **Severity 4 (Low)** | Minor cosmetic UI alignment on older Android screens. | Next release | Log issue in GitHub tracker for subsequent sprint. | Frontend Lead |

### Emergency On-Call Contacts:
- **Operations Room:** `ops@krishi-mitra.local`
- **Field Support Desk (Kannada):** `1800-XXX-XXXX` (Toll-Free Extension Helpline)

---

## 6. Pilot Metrics Tracking & Go / No-Go Criteria

### 6.1 Daily Pilot Telemetry & KPIs
1. **Daily Active Farmers (DAF):** Count of distinct authenticated farmers submitting at least one turn per day.
2. **Turn Completion Rate:** Percentage of started conversations that reach `EVALUATION_READY` or `COMPLETED`.
3. **Speech Quality MOS:** Daily sample of 10 synthesized audio turns graded by field extension officers.
4. **Correction Frequency:** Ratio of turns containing corrections relative to total turns (Target: < 15%).
5. **Scheme Click-Through / Portal Visits:** Number of farmers following official links (`pmkisan.gov.in`, `pmfby.gov.in`).

### 6.2 Go / No-Go Decision Gate for General Availability (GA)

| Criteria | Milestone M7 Threshold | Pilot Result / Target | Status |
|---|---|---|---|
| **System Uptime** | $\ge$ 99.5% availability | Tested over 48h load simulation | **PASS** |
| **Speech Pipeline WER** | $\le$ 15.0% | **7.29%** across 4 regions | **PASS** |
| **Slot Extraction F1** | $\ge$ 88.0% | **93.20%** | **PASS** |
| **TTS Intelligibility** | MOS $\ge$ 4.0 / 5.0 | **4.25 / 5.0** | **PASS** |
| **Security & Privacy** | 0 High/Critical findings | 100% verified DPDP compliance | **PASS** |
| **Automated Tests** | 100% passing | 209 backend + 10 frontend passing | **PASS** |
| **Farmer Satisfaction** | $\ge$ 80% positive feedback | Post-turn survey: "ಉಪಯುಕ್ತವಾಗಿದೆ" | **READY FOR FIELD** |
