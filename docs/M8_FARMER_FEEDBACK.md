# Krishi Mitra — Milestone M8: Farmer Usability Requirements & Illustrative Feedback Analysis

**Document Status:** Corrected Technical Report  
**Evidence Classification:** `DOCUMENTED_PROCEDURE` & `SYNTHETIC_SPECIMEN`  
**Prior Classification Status:** REVOKED (Prior claims of 20 live farmer interviews and Likert survey scores were unverified synthetic representations)  
**Governing Standard:** ISO/IEC 25010 Usability & Digital Personal Data Protection (DPDP) Act, 2023  
**Implementation Baseline:** M7 `f7e5575573f700f262c0a6ae4e4849d0f11163e2` | Branch: `fix/m8-evidence-integrity`  

---

> [!IMPORTANT]
> **EVIDENCE INTEGRITY DISCLOSURE (AUDIT STATEMENT):**  
> **Zero real human farmers were interviewed, surveyed, or recorded for Milestone M8.**  
> The previous revision of this document presented synthetic design personas, illustrative dialogue specimens, and simulated usability ratings as genuine field observations. Under CTO engineering direction (M8.6), all fabricated identities, unsupported quotations, and synthetic survey percentages have been completely revoked and reclassified.  
> 
> Real-world farmer testing is strictly governed by the protocol established in [`M8_REAL_FIELD_PILOT_PROTOCOL.md`](file:///C:/Users/shash/OneDrive/Desktop/PROJECTS/Voice-Assistant/docs/M8_REAL_FIELD_PILOT_PROTOCOL.md) and requires approved informed consent under [`M8_FARMER_FEEDBACK_TEMPLATE.md`](file:///C:/Users/shash/OneDrive/Desktop/PROJECTS/Voice-Assistant/docs/M8_FARMER_FEEDBACK_TEMPLATE.md).

---

## 1. Executive Summary & Purpose

This document details the **human-centered design requirements**, **regional linguistic specifications**, and **illustrative interaction patterns** developed to guide voice interface development for rural Karnataka farmers.

Rather than claiming unconsented or fabricated empirical field observations, this report serves as the engineering baseline for:
1. Defining the linguistic and dialectal challenges across Karnataka's four principal agricultural zones.
2. Establishing the interaction design principles necessary to prevent false entitlement expectations.
3. Providing pre-pilot usability hypotheses to be formally tested during the upcoming assisted micro-pilot (N = 10–15 consented farmers).

---

## 2. Regional Linguistic Profiles & Illustrative Dialogue Design

Karnataka exhibits pronounced regional variation in Kannada vocabulary, syntax, and agricultural terminology. The conversational AI pipeline is designed around four regional dialect targets.

> [!NOTE]
> The dialogue snippets below are **synthetic design specimens** formulated to test natural language understanding (NLU) and text-to-speech (TTS) engines against regional vernacular patterns. They do NOT represent recorded human participants.

### 2.1 North Karnataka (ಉತ್ತರ ಕರ್ನಾಟಕ — ಧಾರವಾಡ, ಬೆಳಗಾವಿ, ಬಾಗಲಕೋಟೆ, ವಿಜಯಪುರ)
- **Linguistic Markers:** Fast conversational cadence, geminated consonants, colloquial sentence particles (*"ರೀ"*, *"ಹೌನ್ರೀ"*, *"ಏನ್ರೀ"*), regional agricultural terms (*"ಹೊಲ"* for farmland, *"ಜೋಳ"* for sorghum, *"ಹೆಸರು"* for green gram, *"ಗುಂಟೆ"* for guntha).
- **Illustrative Persona Specimen (`SF01` / `SF03` Design Target):**
  - *Utterance Pattern:* `"ನಮಸ್ಕಾರ, ಧಾರವಾಡ ಜಿಲ್ಲೆ ನವಲಗುಂದ ತಾಲ್ಲೂಕಿನಲ್ಲಿ 2 ಎಕರೆ ಜಮೀನಿದೆ, ಹೆಸರು ಬೆಳೆದಿದ್ದೇನೆ."`
  - *Design Expectation:* System must extract district `DHARWAD`, taluk `NAVALGUND`, crop `GREEN_GRAM`, and land area `2.0 acres` without requiring formal administrative terminology.
  - *Speech Synthesis Target:* High intelligibility for numbers and technical scheme acronyms; avoidance of overly formal Old Kannada inflection.

### 2.2 Kalyana Karnataka (ಕಲ್ಯಾಣ ಕರ್ನಾಟಕ — ಕಲಬುರಗಿ, ರಾಯಚೂರು, ಬೀದರ್, ಕೊಪ್ಪಳ)
- **Linguistic Markers:** Influence of Dakhni Urdu and Telugu loan words, prolonged vowels, arid-zone pulse terminology (*"ತೊಗರಿ"*, *"ಕಡಲೆ"*, *"ಬೆಳೆ ಹಾಳಾಗಿದೆ"* for crop loss, *"ಪರಿಹಾರ"* for relief).
- **Illustrative Persona Specimen (`SF07` / `SF08` Design Target):**
  - *Utterance Pattern:* `"ಕಲಬುರಗಿ ಆಳಂದ ತಾಲೂಕಿನಲ್ಲಿ ಮಳೆಯಿಲ್ಲದೆ 6 ಎಕರೆ ತೊಗರಿ ಬೆಳೆ ಹಾಳಾಗಿದೆ, ಪರಿಹಾರ ಸಿಗಬಹುದಾ?"`
  - *Design Expectation:* Intent must route to `CROP_INSURANCE` / `PMFBY` with explicit disclosure that payouts require official crop-cutting experiment (CCE) damage surveys.

### 2.3 South Karnataka (ಹಳೇ ಮೈಸೂರು — ಮಂಡ್ಯ, ಮೈಸೂರು, ಹಾಸನ, ಚಾಮರಾಜನಗರ)
- **Linguistic Markers:** Honorific respectful markers (*"ಸ್ವಾಮಿ"*, *"ಬುದ್ಧಿ"*), wetland agricultural terms (*"ಗದ್ದೆ"* for paddy land, *"ಕಬ್ಬು"* for sugarcane, *"ರಾಗಿ"* for finger millet).
- **Illustrative Persona Specimen (`SF12` / `SF16` Design Target):**
  - *Utterance Pattern:* `"ಮಂಡ್ಯ ಜಿಲ್ಲೆ ಮದ್ದೂರು ತಾಲೂಕಿನಲ್ಲಿ 2 ಎಕರೆ ಕಬ್ಬಿನ ಗದ್ದೆ ಇದೆ."`
  - *Design Expectation:* System must canonicalize *"ಕಬ್ಬಿನ ಗದ್ದೆ"* into crop `SUGARCANE` and land unit `ACRES`, disambiguating `"ಗದ್ದೆ"` (wetland) from `"ಹೊಲ"` (dryland).

### 2.4 Coastal Karnataka (ಕರಾವಳಿ ಕನ್ನಡ — ಉಡುಪಿ, ದಕ್ಷಿಣ ಕನ್ನಡ, ಉತ್ತರ ಕನ್ನಡ)
- **Linguistic Markers:** Distinct intonational contours, plantation horticulture vocabulary (*"ಅಡಿಕೆ ತೋಟ"*, *"ತೆಂಗು"*, *"ಮುಂಗಾರು ಭತ್ತ"*, *"ಹನಿ ನೀರಾವರಿ"*).
- **Illustrative Persona Specimen (`SF17` / `SF19` Design Target):**
  - *Utterance Pattern:* `"ಉತ್ತರ ಕನ್ನಡ ಜಿಲ್ಲೆ ಶಿರಸಿ ತಾಲೂಕಿನಲ್ಲಿ 2 ಎಕರೆ ಅಡಿಕೆ ತೋಟ ಇದೆ, ಹನಿ ನೀರಾವರಿ ಸಹಾಯಧನ ಬೇಕು."`
  - *Design Expectation:* System must route to `MICRO_IRRIGATION` assistance, isolate synthetic demonstration rules with visual and auditory `DEMO_ONLY` warnings, and preserve plantation terminology.

---

## 3. Institutional Trust & Safety Design Dimensions

Field interactions in rural public computing consistently show that algorithmic tools risk generating rumors if users perceive informational queries as official benefit guarantees. The following safeguards are built into Krishi Mitra:

| Dimension | Engineering Invariant | Classification | Rationale |
| :--- | :--- | :--- | :--- |
| **Official Portals Citation** | Every scheme card displays its official government portal (e.g. *Kutumba, FRUITS, PM-KISAN, Seva Sindhu*). | `DOCUMENTED_PROCEDURE` | Establishes institutional lineage and prevents confusion with private financial apps. |
| **Verification Caveats** | When recommending benefits based on self-reported facts, the assistant must state: *"ಈ ಮಾಹಿತಿಯು ನಿಮ್ಮ ಸ್ವಂತ ಹೇಳಿಕೆಯನ್ನು ಆಧರಿಸಿದೆ, ಅಂತಿಮ ಮಂಜೂರಾತಿಗೆ ಇಲಾಖೆಯ ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ."* | `DOCUMENTED_PROCEDURE` | Eliminates false hope of automatic financial disbursements. |
| **Tenant Farmer Gating** | Landowner-restricted schemes (e.g. PM-KISAN, Raitha Siri) must explicitly exclude tenant farmers (`ownership == 'TENANT'`) and route them to institutional Kisan Credit Card (KCC) crop loans. | `AUTOMATED_TEST` (Verified in Task 8) | Prevents fraudulent or invalid applications at village service centers. |
| **Synthetic Demo Isolation** | Internal test schemes (e.g. `DEMO_MICRO_IRRIGATION`) must carry an unambiguous visual and spoken badge: `"ಡೆಮೋ ಯೋಜನೆ (ಪ್ರದರ್ಶನಕ್ಕಾಗಿ ಮಾತ್ರ)"`. | `AUTOMATED_TEST` (Verified in Task 8) | Precludes village rumors regarding unverified or fictional subsidies. |

---

## 4. Pre-Pilot Usability Hypotheses & Engineering Mitigations

Prior to the supervised micro-pilot with real farmers, engineering analysis identified three critical user-experience friction points that must be empirically measured:

### 4.1 Microphone Interaction Friction: Tap vs. Press-and-Hold
- **Hypothesis:** Rural smartphone users accustomed to WhatsApp voice messaging may attempt to press-and-hold the microphone button, releasing it prematurely before completing their sentence.
- **Engineering Mitigation:**
  1. Frontend PWA supports both tap-to-record (with visual pulsing ring and recording timer) and press-and-hold interaction modes.
  2. Audio capture starts upon touchstart and concludes on touchend or manual toggle, with a 300ms debounce buffer.
  3. Prominent Kannada instruction: `"ಮಾತನಾಡಲು ಮೈಕ್ ಒತ್ತಿ"` (Press mic to speak).

### 4.2 Fractional Acreage Verbalization: Decimals vs. Traditional Guntas
- **Hypothesis:** When synthesized TTS outputs decimal acreage (e.g. *"2.25 ಎಕರೆ"*), rural listeners experience cognitive confusion compared to traditional local units (*"2 ಎಕರೆ 10 ಗುಂಟೆ"*).
- **Engineering Mitigation:**
  - The Kannada NLG text normalizer translates floating-point acres into regional compound units during dialogue response synthesis:
    - `0.25 acres` $\rightarrow$ *"10 ಗುಂಟೆ"*
    - `0.50 acres` $\rightarrow$ *"20 ಗುಂಟೆ / ಅರ್ಧ ಎಕರೆ"*
    - `1.50 acres` $\rightarrow$ *"ಒಂದೂವರೆ ಎಕರೆ"*
    - `2.75 acres` $\rightarrow$ *"2 ಎಕರೆ 30 ಗುಂಟೆ"*

### 4.3 Outdoor High-Contrast Sunlight Readability
- **Hypothesis:** Standard mobile app palettes (light grays, subtle borders) wash out under intense direct field sunlight in rural Karnataka.
- **Engineering Mitigation:**
  - High-contrast visual tokens: Primary forest green (`#1B5E20`), deep slate text (`#0F172A`), white background (`#FFFFFF`), with contrast ratios exceeding WCAG AAA standards (minimum 7:1).
  - Minimum touch target size: $48 \times 48\,\text{dp}$ for all interactive buttons.

---

## 5. Formal Micro-Pilot Feedback Plan

Empirical farmer feedback will be collected during the upcoming **Stage 2 Supervised Micro-Pilot** (N = 10–15 consented farmers).

The evaluation methodology strictly follows:
1. Written/witnessed oral informed consent per [`M8_FARMER_FEEDBACK_TEMPLATE.md`](file:///C:/Users/shash/OneDrive/Desktop/PROJECTS/Voice-Assistant/docs/M8_FARMER_FEEDBACK_TEMPLATE.md).
2. Independent observation and failure logging per [`M8_REAL_FIELD_PILOT_PROTOCOL.md`](file:///C:/Users/shash/OneDrive/Desktop/PROJECTS/Voice-Assistant/docs/M8_REAL_FIELD_PILOT_PROTOCOL.md).
3. Post-pilot agronomic audit by a certified Karnataka extension specialist before any qualitative results are published as field evidence.
