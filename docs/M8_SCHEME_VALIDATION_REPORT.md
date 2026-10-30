# Krishi Mitra — Milestone M8: Scheme Validation & Domain Governance Report

**Document Version:** 1.0.0  
**Domain Authority:** Senior Agricultural Domain & Scheme Governance Review  
**Milestone:** M8 — Controlled Farmer Pilot & Field Validation  
**Baseline Engine:** Deterministic Rule Engine (`app/core/scheme/engine.py` & `app/services/recommendation_service.py`)  
**Audit Dataset:** 20 Pilot Farmer Evaluations (`docs/pilot_field_metrics.json`)  

---

## 1. Executive Summary & Non-Negotiable Invariants

The primary role of Krishi Mitra's recommendation engine is to deliver **deterministic, auditable, evidence-backed agricultural guidance** without delegating eligibility decisions to generative AI models.

During Milestone M8, all recommendations generated for the 20 pilot participants were subjected to rigorous agricultural domain inspection and statutory compliance audits.

### Non-Negotiable Architectural & Legal Invariants:
1. **Zero LLM Rule Evaluation:** Under no circumstances does an LLM evaluate scheme logic, grant eligibility, or calculate benefits. All evaluations execute via Python AST rule engines against versioned schemas.
2. **Mandatory Official Verification Caveat:** Every genuine government scheme recommendation based on self-reported farmer statements carries the strict caveat: `official_verification_required: true`. Recommendations are advisory guides, never administrative sanctions.
3. **PMFBY Seasonal & Taluk Blocking:** Pradhan Mantri Fasal Bima Yojana (PMFBY) is blocked or gated with verification requirements wherever current seasonal notifications and insurance company cluster allocations remain unverified for the specific taluk and crop.
4. **Tenant Farmer Exclusion Enforcement:** Tenant farmers (`land_ownership: "TENANT"`) are deterministically barred from land-ownership subsidies (PM-KISAN, borewell subsidies) and directed strictly to credit/crop loan programs.
5. **Absolute Synthetic Scheme Isolation:** Demonstration schemes (e.g., `DEMO_MICRO_IRRIGATION`) are strictly labeled `classification: "SYNTHETIC_DEMO"` and `demo_only: true`. They are prohibited from being combined with genuine public benefit claims.

---

## 2. Scheme-by-Scheme Domain Validation

### 2.1 Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)
- **Official Authority:** Ministry of Agriculture & Farmers Welfare, Government of India.
- **Official Source Portal:** `https://pmkisan.gov.in/`
- **Rule Version:** `1.0.0` (Verified).
- **Core Eligibility Criteria:**
  - Land ownership: Must be a recorded landholder (`land_ownership == "OWNER"`).
  - Maximum landholding: Cultivable landholding (small and marginal priority; institutional landholders excluded).
  - Exclusions: Institutional landholders, constitutional post holders, serving/retired government officers, income tax payees.
- **Field Trial Evaluation Findings:**
  - **Landowner Validation (17 Farmers):** All 17 landowner participants qualifying by acreage received PM-KISAN recommendations. Every card displayed:
    - Benefit: ₹6,000 per annum in three equal installments of ₹2,000 directly into Aadhaar-seeded bank accounts (DBT).
    - Verification Caveat: *"ಭೂ ದಾಖಲೆ (RTC/ಪಹಣಿ) ಮತ್ತು ಇ-ಕೆವೈಸಿ (e-KYC) ಕಂದಾಯ ಇಲಾಖೆಯ ಪರಿಶೀಲನೆಗೆ ಒಳಪಟ್ಟಿರುತ್ತದೆ."*
  - **Tenant Validation (3 Farmers — F03, F08, F16):**
    - Correctly excluded with reason: *"ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ಯೋಜನೆಯು ಕೇವಲ ಸ್ವಂತ ಭೂಮಿ ಹೊಂದಿರುವ ರೈತರಿಗೆ ಮಾತ್ರ ಅನ್ವಯಿಸುತ್ತದೆ. ಗೇಣಿ ರೈತರಿಗೆ ಈ ಸೌಲಭ್ಯ ಲಭ್ಯವಿರುವುದಿಲ್ಲ."*
    - Zero tenant farmers wrongfully qualified for PM-KISAN.

### 2.2 Pradhan Mantri Fasal Bima Yojana (PMFBY)
- **Official Authority:** Department of Agriculture & Farmers Welfare, GoI & GoK.
- **Official Source Portal:** `https://samrakshane.karnataka.gov.in/`
- **Verification Status:** `INCOMPLETE` / `STALE` for unnotified off-season taluks.
- **Governance Constraint:** Crop insurance notifications are published each season on the Samrakshane portal, specifying notified crops per Gram Panchayat and insurance unit. In the absence of an active real-time API integration to Samrakshane:
  - PMFBY **must not** display unconditional approval.
  - The recommendation must be flagged with `official_verification_required: true` and state that notification depends on the current season (Kharif / Rabi).
- **Field Trial Evaluation Findings:**
  - Participants inquiring about crop damage (e.g., F07 in Aland, Kalaburagi; F20 in Kundapura, Udupi) received PMFBY insurance information with the mandatory caveat:
    - *"ಬೆಳೆ ವಿಮೆ ಲಭ್ಯತೆಯು ಪ್ರಸ್ತುತ ಹಂಗಾಮಿನ ಅಧಿಸೂಚಿತ ಬೆಳೆ ಮತ್ತು ಗ್ರಾಮ ಪಂಚಾಯತಿ ವ್ಯಾಪ್ತಿಯನ್ನು ಅವಲಂಬಿಸಿರುತ್ತದೆ. Samrakshane ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪರಿಶೀಲನೆ ಕಡ್ಡಾಯ."*
  - Zero unconditional insurance claims were emitted.

### 2.3 Raitha Siri Scheme (ರೈತ ಸಿರಿ ಯೋಜನೆ)
- **Official Authority:** Department of Agriculture, Government of Karnataka.
- **Official Source Portal:** `https://raitamitra.karnataka.gov.in/`
- **Rule Version:** `1.0.0` (Verified).
- **Core Eligibility Criteria:**
  - Cultivation of specified minor millets (ಸಜ್ಜೆ/Pearl Millet, ರಾಗಿ/Finger Millet, ಸಿರಿಧಾನ್ಯಗಳು).
  - Area: Up to maximum 2 hectares (5 acres).
  - Incentive: ₹10,000 per hectare (direct cash incentive for millet cultivation).
- **Field Trial Evaluation Findings:**
  - Farmer F11 (Koppal, pearl millet/ಸಜ್ಜೆ, 2 acres) and Farmer F14/F15 (Hassan/Mandya, ragi, 3–4 acres) correctly matched Raitha Siri.
  - Benefit and documentation requirements (FRUITS registration, crop survey verification) were accurately detailed in Kannada.

### 2.4 Krishi Bhagya Scheme (ಕೃಷಿ ಭಾಗ್ಯ ಯೋಜನೆ)
- **Official Authority:** Department of Agriculture, Government of Karnataka.
- **Target Geography:** Rainfed dryland agro-climatic zones (North & Kalyana Karnataka dryland districts).
- **Component:** Farm pond construction (ಕೃಷಿ ಹೊಂಡ), polythene lining, diesel pumpsets.
- **Field Trial Evaluation Findings:**
  - Farmers in dryland districts (Dharwad, Belagavi, Vijayapura, Kalaburagi) matched the regional criteria.
  - Wetlands and canal-irrigated farmers in Mandya (F12) were appropriately deprioritized for farm pond rainwater harvesting subsidies.

### 2.5 Synthetic Demonstration Scheme (DEMO_MICRO_IRRIGATION)
- **Classification:** `SYNTHETIC_DEMO`.
- **Purpose:** UI and system testing of drip/sprinkler subsidy calculations.
- **Governance Mandate:** Must NEVER appear as a genuine government entitlement.
- **Field Trial Evaluation Findings:**
  - When matched for high-water horticulture farmers (F17 in Sirsi, F12 in Maddur), the output payload explicitly enforced:
    - `classification: "SYNTHETIC_DEMO"`
    - `demo_only: true`
    - Display Badge: *"ಡೆಮೋ ಯೋಜನೆ (ಪ್ರದರ್ಶನಕ್ಕಾಗಿ ಮಾತ್ರ — ಅಧಿಕೃತ ಯೋಜನೆಯಲ್ಲ)"*
  - No synthetic scheme was presented as a real government benefit.

---

## 3. Exclusion Matrix & Tenant Farmer Protection

A major risk in rural agricultural software is misleading vulnerable tenant farmers or inducing them to incur debt based on false expectations of government subsidies. The table below confirms deterministic enforcement of exclusion rules:

| Farmer ID | District & Region | Land Holding (Acres) | Ownership Status | Primary Crop | Excluded Schemes & Verified Rationale |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **F03** | Bagalkote (North) | 2.0 | **TENANT (ಗೇಣಿ)** | Sorghum (ಜೋಳ) | **Excluded from PM-KISAN:** Fails mandatory land title (RTC) requirement. Guided to tenant crop loans. |
| **F08** | Kalaburagi (Kalyana) | 2.5 | **TENANT (ಗೇಣಿ)** | Cotton (ಹತ್ತಿ) | **Excluded from PM-KISAN:** Non-owner status. Guided to interest subvention credit. |
| **F16** | Chamarajanagar (South) | 2.5 | **TENANT (ಗೇಣಿ)** | Ragi (ರಾಗಿ) | **Excluded from PM-KISAN:** Non-owner status. Recommended NABARD joint liability group loans. |
| **F07** | Kalaburagi (Kalyana) | 6.0 | **OWNER (ಸ್ವಂತ)** | Pigeon Pea (ತೊಗರಿ) | **Excluded from Small/Marginal Subsidies:** Exceeds 5-acre threshold for 90% farm pond subsidies (categorized under general 50% tier). |

---

## 4. Audit Trail & Deterministic Trace Verification

Under Directive M4 and M5, every scheme evaluation creates an immutable, cryptographically verifiable recommendation audit trace in the database (`scheme_recommendation_traces`).

### 4.1 Trace Structure Audit
Each trace records:
- `trace_id`: UUID primary key.
- `farmer_id`: Anonymized farmer identifier.
- `rule_version`: Cryptographic SHA-256 hash of the exact rule definition active at evaluation time.
- `input_profile_snapshot`: JSON snapshot of the asserted agricultural slots (district, crop, acres, ownership).
- `evaluation_results`: Granular boolean results for each eligibility clause and exclusion clause.
- `evaluation_timestamp`: UTC ISO timestamp.

### 4.2 Immutability & Forensic Auditability
- In the event of a dispute (e.g., a farmer asking why they were deemed ineligible for a scheme), the exact rule version, input facts, and clause-by-clause boolean evaluations can be reconstructed with 100% mathematical determinism.
- The evaluation does not change across system restarts or model updates because it executes pure Python code against static rule schemas.

---

## 5. Domain Governance Sign-Off

The domain review concludes that the Krishi Mitra recommendation engine strictly adheres to agricultural policy guidelines, accurately protects tenant farmers, isolates synthetic demonstration records, and enforces transparent official verification disclaimers across all outputs.
